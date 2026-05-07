from app.db.models import ResearchItem
from app.engines.llm_client import enhance_verdict
from app.engines.schemas import EngineResult, clamp
from app.engines.utils import text_blob

DOMAIN_KEYWORDS = {
    "biology": ["protein", "genome", "biology", "molecule", "drug"],
    "healthcare": ["hospital", "clinical", "medical", "healthcare", "patient"],
    "finance": ["finance", "trading", "risk", "portfolio", "fraud"],
    "robotics": ["robot", "navigation", "control", "manipulation"],
    "supply chain": ["supply chain", "logistics", "inventory", "routing"],
    "education": ["education", "tutor", "student", "learning"],
    "security": ["security", "adversarial", "attack", "defense"],
}

TECHNIQUE_KEYWORDS = [
    "graph neural",
    "message passing",
    "routing",
    "retrieval",
    "diffusion",
    "transformer",
    "agent",
    "reinforcement learning",
    "causal",
    "multimodal",
]


class CrossDomainEngine:
    def score(self, item: ResearchItem, related_items: list[ResearchItem]) -> EngineResult:
        metadata = item.extra_metadata or {}
        blob = text_blob(item)
        source_domain = metadata.get("source_domain")
        target_domain = metadata.get("target_domain")
        technique = metadata.get("technique")

        inferred_domains = self._infer_domains(blob)
        inferred_techniques = [tech for tech in TECHNIQUE_KEYWORDS if tech in blob]

        if not source_domain and inferred_domains:
            source_domain = inferred_domains[0]
        if not target_domain and len(inferred_domains) > 1:
            target_domain = inferred_domains[1]
        if not technique and inferred_techniques:
            technique = inferred_techniques[0]

        related_domain_hits = 0
        for related in related_items:
            related_domains = self._infer_domains(text_blob(related))
            if source_domain and any(domain != source_domain for domain in related_domains):
                related_domain_hits += 1

        explicit_bonus = 0.45 if metadata.get("source_domain") and metadata.get("target_domain") else 0.0
        domain_bonus = 0.25 if source_domain and target_domain and source_domain != target_domain else 0.0
        technique_bonus = 0.2 if technique else 0.0
        related_bonus = min(related_domain_hits / 5, 0.25)
        score = clamp(explicit_bonus + domain_bonus + technique_bonus + related_bonus)

        evidence = []
        if source_domain and target_domain:
            evidence.append(f"Potential transfer path detected: {source_domain} → {target_domain}.")
        if technique:
            evidence.append(f"Transferable technique candidate: {technique}.")
        if related_domain_hits:
            evidence.append(f"Found {related_domain_hits} related items with cross-domain domain hints.")
        if not evidence:
            evidence.append("No strong cross-domain transfer signal found yet.")

        if score >= 0.7:
            verdict = "Strong cross-domain spark with a plausible transfer mechanism."
        elif score >= 0.4:
            verdict = "Moderate cross-domain opportunity worth exploring."
        else:
            verdict = "Low cross-domain transfer signal in the current corpus."

        verdict, evidence = enhance_verdict(
            engine_name="CrossDomainEngine",
            heuristic_verdict=verdict,
            heuristic_score=score,
            item_title=item.title,
            item_abstract=item.abstract or "",
            evidence_points=evidence,
            extra_context=f"source_domain={source_domain}, target_domain={target_domain}, technique={technique}",
        )

        return EngineResult(
            score=round(score, 4),
            verdict=verdict,
            evidence=evidence,
            details={"source_domain": source_domain, "target_domain": target_domain, "technique": technique},
        )

    def _infer_domains(self, blob: str) -> list[str]:
        domains = []
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in blob for keyword in keywords):
                domains.append(domain)
        return domains
