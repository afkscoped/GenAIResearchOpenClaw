from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from app.db.models import ResearchItem
from app.engines.llm_client import enhance_verdict
from app.engines.schemas import EngineResult, clamp
from app.engines.utils import text_blob

# ---------------------------------------------------------------------------
# Domain taxonomy — each domain has primary keywords (weighted 1.0) and
# secondary/adjacent keywords (weighted 0.5) so frequency matters.
# ---------------------------------------------------------------------------

@dataclass
class DomainSpec:
    primary: list[str]
    secondary: list[str] = field(default_factory=list)


DOMAIN_SPECS: dict[str, DomainSpec] = {
    "biology": DomainSpec(
        primary=["protein", "genome", "genomic", "proteomic", "molecular biology",
                 "gene expression", "enzyme", "dna", "rna", "cell"],
        secondary=["biological", "organism", "metabolic", "biochemical", "drug", "molecule"],
    ),
    "healthcare": DomainSpec(
        primary=["clinical trial", "patient", "diagnosis", "medical imaging",
                 "electronic health record", "ehr", "disease", "therapy"],
        secondary=["hospital", "healthcare", "medical", "physician", "prognosis",
                   "treatment", "radiology"],
    ),
    "finance": DomainSpec(
        primary=["portfolio", "equity", "stock market", "algorithmic trading",
                 "credit risk", "derivative", "asset pricing"],
        secondary=["finance", "trading", "risk", "fraud", "financial", "investment", "return"],
    ),
    "robotics": DomainSpec(
        primary=["robot", "autonomous vehicle", "manipulation", "path planning",
                 "sim-to-real", "actuator", "kinematics"],
        secondary=["navigation", "control system", "sensor fusion", "localization", "servo"],
    ),
    "supply chain": DomainSpec(
        primary=["supply chain", "inventory management", "demand forecasting",
                 "warehouse", "last-mile delivery"],
        secondary=["logistics", "routing", "procurement", "vendor", "fulfillment"],
    ),
    "education": DomainSpec(
        primary=["student performance", "intelligent tutoring", "curriculum",
                 "adaptive learning", "knowledge tracing"],
        secondary=["education", "tutor", "student", "learning", "classroom", "pedagogy"],
    ),
    "security": DomainSpec(
        primary=["adversarial attack", "intrusion detection", "malware",
                 "vulnerability", "cryptography", "threat model"],
        secondary=["security", "defense", "attack", "cyber", "exploit", "authentication"],
    ),
    "nlp": DomainSpec(
        primary=["natural language processing", "text classification", "named entity",
                 "sentiment analysis", "machine translation", "question answering"],
        secondary=["language model", "tokenization", "embedding", "corpus", "nlp"],
    ),
    "computer vision": DomainSpec(
        primary=["image classification", "object detection", "semantic segmentation",
                 "convolutional neural network", "cnn", "image recognition"],
        secondary=["vision", "visual", "pixel", "feature map", "bounding box"],
    ),
}

# ---------------------------------------------------------------------------
# Technique taxonomy — techniques that are domain-transferable carry higher
# transfer potential.
# ---------------------------------------------------------------------------

TECHNIQUE_SPECS: dict[str, float] = {
    # High-transfer — architecture-agnostic methods
    "graph neural network": 1.0,
    "message passing": 1.0,
    "diffusion model": 1.0,
    "transformer": 0.9,
    "attention mechanism": 0.9,
    "contrastive learning": 0.9,
    "meta-learning": 1.0,
    "transfer learning": 1.0,
    "reinforcement learning": 0.85,
    "causal inference": 0.9,
    "retrieval augmented": 0.85,
    "multimodal": 0.8,
    # Moderate-transfer
    "neural network": 0.6,
    "deep learning": 0.6,
    "embedding": 0.65,
    "self-supervised": 0.75,
    "few-shot": 0.8,
    "zero-shot": 0.8,
    "knowledge distillation": 0.7,
    "federated learning": 0.75,
}

# Score weights — must sum to 1.0
_W_DOMAIN_PAIR = 0.35    # Explicit or inferred source→target domain pair
_W_TECHNIQUE   = 0.30    # Identified transferable technique
_W_RELATED     = 0.20    # Related-item cross-domain corroboration
_W_DENSITY     = 0.15    # Keyword density / richness of cross-domain signal


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for reliable matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _score_domain(blob: str, spec: DomainSpec) -> float:
    """
    Return a [0, 1] relevance score for a domain given the text blob.
    Uses term frequency with primary/secondary weighting so a paper that
    mentions a keyword 5 times scores higher than one that mentions it once.
    """
    score = 0.0
    for kw in spec.primary:
        count = len(re.findall(r"\b" + re.escape(kw) + r"\b", blob))
        score += min(count * 1.0, 3.0)   # cap single-term contribution
    for kw in spec.secondary:
        count = len(re.findall(r"\b" + re.escape(kw) + r"\b", blob))
        score += min(count * 0.5, 1.5)
    # Normalise against a "rich" paper ceiling (~10 total points)
    return min(score / 10.0, 1.0)


def _rank_domains(blob: str) -> list[tuple[str, float]]:
    """Return all domains sorted by relevance score, highest first."""
    scores = {domain: _score_domain(blob, spec) for domain, spec in DOMAIN_SPECS.items()}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(d, s) for d, s in ranked if s > 0]


def _best_technique(blob: str) -> tuple[str | None, float]:
    """Return the highest-weight technique found in the blob."""
    best_name, best_weight = None, 0.0
    for tech, weight in TECHNIQUE_SPECS.items():
        if re.search(r"\b" + re.escape(tech) + r"\b", blob):
            if weight > best_weight:
                best_name, best_weight = tech, weight
    return best_name, best_weight


class CrossDomainEngine:
    """
    Scores a ResearchItem on its cross-domain transfer potential.

    Scoring philosophy
    ------------------
    Four independent signals are computed and linearly combined with
    fixed weights (see _W_* constants above).  Each signal is in [0, 1].

    1. domain_pair_score  — how confidently we can identify a source domain
                            AND a distinct target domain.
    2. technique_score    — presence of a known transferable technique,
                            scaled by that technique's transferability weight.
    3. related_score      — fraction of related papers that independently show
                            cross-domain signals beyond the source domain.
    4. density_score      — how many distinct domains appear in the text,
                            rewarding papers with genuinely broad scope.
    """

    def score(self, item: ResearchItem, related_items: list[ResearchItem]) -> EngineResult:
        metadata = item.extra_metadata or {}
        blob = _normalize(text_blob(item))

        # ── 1. Determine source / target domains ────────────────────────────
        source_domain: str | None = metadata.get("source_domain")
        target_domain: str | None = metadata.get("target_domain")
        explicit_domains = bool(source_domain and target_domain)

        ranked_domains = _rank_domains(blob)
        domain_scores: dict[str, float] = dict(ranked_domains)

        if not source_domain and ranked_domains:
            source_domain = ranked_domains[0][0]
        if not target_domain:
            # Pick the highest-scoring domain that is different from source
            for domain, _ in ranked_domains:
                if domain != source_domain:
                    target_domain = domain
                    break

        # domain_pair_score: reward distinct source+target, penalise overlap
        if explicit_domains:
            domain_pair_score = 1.0
        elif source_domain and target_domain and source_domain != target_domain:
            # Scale by how strong both domain signals are
            src_s = domain_scores.get(source_domain, 0.0)
            tgt_s = domain_scores.get(target_domain, 0.0)
            domain_pair_score = (src_s + tgt_s) / 2.0
        else:
            domain_pair_score = 0.0

        # ── 2. Technique ────────────────────────────────────────────────────
        technique: str | None = metadata.get("technique")
        technique_weight = 0.0
        if not technique:
            technique, technique_weight = _best_technique(blob)
        else:
            # Explicit metadata — look up its weight or give a baseline
            technique_weight = TECHNIQUE_SPECS.get(technique.lower(), 0.6)

        technique_score = technique_weight  # already in [0, 1]

        # ── 3. Related-item corroboration ───────────────────────────────────
        related_cross_domain_count = 0
        for related in related_items:
            related_blob = _normalize(text_blob(related))
            related_ranked = _rank_domains(related_blob)
            related_domain_names = {d for d, s in related_ranked if s > 0.15}
            # A related item is a real corroborator only if it spans ≥2 domains
            # AND at least one domain differs from the item's source domain.
            if len(related_domain_names) >= 2 and source_domain not in related_domain_names or (
                source_domain in related_domain_names and len(related_domain_names) >= 2
                and any(d != source_domain for d in related_domain_names)
            ):
                related_cross_domain_count += 1

        related_score = min(related_cross_domain_count / max(len(related_items), 1), 1.0)

        # ── 4. Density — breadth of domain signals in the text ──────────────
        # Count distinct domains with a non-trivial signal (>0.1)
        active_domains = [d for d, s in ranked_domains if s > 0.1]
        density_score = min(len(active_domains) / 4.0, 1.0)  # 4+ domains → full score
        domain_score_details = [
            {"domain": domain, "score": round(domain_score, 3)}
            for domain, domain_score in ranked_domains
        ]
        candidate_topics = [
            value
            for value in [
                getattr(item, "topic", None),
                source_domain,
                target_domain,
                technique,
            ]
            if value
        ]

        # ── 5. Composite score ───────────────────────────────────────────────
        score = clamp(
            _W_DOMAIN_PAIR * domain_pair_score
            + _W_TECHNIQUE  * technique_score
            + _W_RELATED    * related_score
            + _W_DENSITY    * density_score
        )

        # ── 6. Evidence ─────────────────────────────────────────────────────
        evidence: list[str] = []

        if source_domain and target_domain:
            label = "Explicit" if explicit_domains else "Inferred"
            src_pct = f"{domain_scores.get(source_domain, 0):.0%}"
            tgt_pct = f"{domain_scores.get(target_domain, 0):.0%}"
            evidence.append(
                f"{label} transfer path: {source_domain} ({src_pct} signal) "
                f"→ {target_domain} ({tgt_pct} signal)."
            )

        if technique:
            evidence.append(
                f"Transferable technique: '{technique}' "
                f"(transferability weight: {technique_weight:.2f})."
            )

        if active_domains:
            evidence.append(
                f"Domain breadth: {len(active_domains)} active domain(s) detected "
                f"({', '.join(active_domains)})."
            )

        if related_cross_domain_count:
            evidence.append(
                f"{related_cross_domain_count}/{len(related_items)} related items show "
                "independent cross-domain signals."
            )

        if not evidence:
            evidence.append("No strong cross-domain transfer signal found in the current corpus.")

        # ── 7. Verdict ───────────────────────────────────────────────────────
        if score >= 0.72:
            verdict = "Strong cross-domain spark with a plausible, well-supported transfer mechanism."
        elif score >= 0.45:
            verdict = "Moderate cross-domain opportunity — transfer path exists but needs validation."
        elif score >= 0.2:
            verdict = "Weak cross-domain signal — domain hints present but technique or target unclear."
        else:
            verdict = "Low cross-domain transfer signal in the current corpus."

        verdict, evidence = enhance_verdict(
            engine_name="CrossDomainEngine",
            heuristic_verdict=verdict,
            heuristic_score=score,
            item_title=item.title,
            item_abstract=item.abstract or "",
            evidence_points=evidence,
            extra_context=(
                f"source_domain={source_domain}, target_domain={target_domain}, "
                f"technique={technique}, domain_pair_score={domain_pair_score:.3f}, "
                f"technique_score={technique_score:.3f}, related_score={related_score:.3f}, "
                f"density_score={density_score:.3f}"
            ),
        )

        return EngineResult(
            score=round(score, 4),
            verdict=verdict,
            evidence=evidence,
            details={
                "source_domain": source_domain,
                "target_domain": target_domain,
                "technique": technique,
                "technique_weight": round(technique_weight, 3),
                "domain_pair_score": round(domain_pair_score, 3),
                "technique_score": round(technique_score, 3),
                "related_score": round(related_score, 3),
                "density_score": round(density_score, 3),
                "active_domains": active_domains,
                "domain_scores": domain_score_details,
                "candidate_topics": list(dict.fromkeys(candidate_topics)),
                "transfer_path": {
                    "source": source_domain,
                    "target": target_domain,
                },
            },
        )

    # kept for external callers that may use it directly
    def _infer_domains(self, blob: str) -> list[str]:
        return [d for d, _ in _rank_domains(_normalize(blob))]
