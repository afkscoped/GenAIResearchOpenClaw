#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/smoke_test.py
---------------------
End-to-end integration smoke-test for PRISM persistent engine storage.

Usage (from the repo root, with the backend venv active):

    # Start the server first (separate terminal):
    #   cd backend && uvicorn app.main:app --reload --port 8000
    #
    # Then run this script:
    python scripts/smoke_test.py

The script will:
  1. Run the ingestion pipeline to seed some research items.
  2. Pick the first available item.
  3. Call POST /api/analysis/run-engines to persist an EngineRun + FusionReportRecord.
  4. Call GET  /api/analysis/engine-runs/{item_id}   to retrieve stored runs.
  5. Call GET  /api/analysis/fusion-history/{item_id} to retrieve stored fusion history.
  6. Call GET  /api/analysis/fusion-reports/{item_id} to confirm the dynamic
     (non-persisted) endpoint still returns the same shape.
  7. Print a pass/fail summary.

All assertions are explicit so failures surface clearly.
"""

from __future__ import annotations

import io
import sys
from typing import Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests  # noqa: E402

BASE = "http://127.0.0.1:8000"
TIMEOUT = 30

# ANSI colours for readability
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{RESET}  {msg}")


def _fail(msg: str) -> None:
    print(f"  {RED}[FAIL]{RESET}  {msg}")
    sys.exit(1)


def _section(title: str) -> None:
    print(f"\n{BOLD}{'-' * 60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'-' * 60}{RESET}")


def check(condition: bool, msg: str) -> None:
    if condition:
        _ok(msg)
    else:
        _fail(msg)


# ---------------------------------------------------------------------------
# Step 1 – health check
# ---------------------------------------------------------------------------
_section("Step 1 · Health check")
r = requests.get(f"{BASE}/health", timeout=TIMEOUT)
check(r.status_code == 200, f"GET /api/health → {r.status_code}")
data = r.json()
check(data.get("status") == "ok", f"status=ok  (got {data!r})")

# ---------------------------------------------------------------------------
# Step 2 – run ingestion pipeline to seed items
# ---------------------------------------------------------------------------
_section("Step 2 · Run ingestion pipeline (seeds research items)")
r = requests.post(
    f"{BASE}/api/run-pipeline",
    params={"query": "multimodal agents", "limit_per_source": 2, "include_demo": True},
    timeout=TIMEOUT,
)
check(r.status_code == 200, f"POST /api/run-pipeline → {r.status_code}")
pipeline_data: dict[str, Any] = r.json()
print(f"         ingested_items   = {pipeline_data.get('ingested_items')}")
print(f"         stored_items     = {pipeline_data.get('stored_items')}")
print(f"         stored_signals   = {pipeline_data.get('stored_signals')}")

# ---------------------------------------------------------------------------
# Step 3 – pick an item
# ---------------------------------------------------------------------------
_section("Step 3 · Pick a ResearchItem")
r = requests.get(f"{BASE}/api/items", params={"limit": 1}, timeout=TIMEOUT)
check(r.status_code == 200, f"GET /api/items → {r.status_code}")
items = r.json()
check(len(items) >= 1, f"At least one item in the database (got {len(items)})")
item_id: str = items[0]["id"]
print(f"         Using item_id    = {item_id!r}")
print(f"         Title            = {items[0].get('title', '')[:70]}")

# ---------------------------------------------------------------------------
# Step 4 – POST /api/analysis/run-engines  (the new persistent endpoint)
# ---------------------------------------------------------------------------
_section("Step 4 · POST /api/analysis/run-engines")
r = requests.post(
    f"{BASE}/api/analysis/run-engines",
    params={"item_id": item_id},
    timeout=TIMEOUT,
)
check(r.status_code == 201, f"POST /api/analysis/run-engines → {r.status_code}")
run_resp: dict[str, Any] = r.json()

# engine_run shape
er = run_resp.get("engine_run", {})
check(isinstance(er.get("id"), int), f"engine_run.id is int  (got {er.get('id')!r})")
check(er.get("item_id") == item_id, f"engine_run.item_id matches ({er.get('item_id')!r})")
for field in ("signal_score", "trust_score", "debate_score", "gap_score", "cross_domain_score"):
    check(
        isinstance(er.get(field), float),
        f"engine_run.{field} is float  (got {er.get(field)!r})",
    )

# fusion_report shape
fr = run_resp.get("fusion_report", {})
check(isinstance(fr.get("id"), int), f"fusion_report.id is int  (got {fr.get('id')!r})")
check(fr.get("item_id") == item_id, f"fusion_report.item_id matches")
check(fr.get("engine_run_id") == er["id"], f"fusion_report.engine_run_id == engine_run.id")
for field in ("prism_score", "novelty_score", "trust_score", "controversy_score",
              "adoption_gap_score", "transferability_score"):
    check(
        isinstance(fr.get(field), float),
        f"fusion_report.{field} is float",
    )
check(isinstance(fr.get("verdict"), str) and len(fr["verdict"]) > 0, "fusion_report.verdict non-empty str")
check(isinstance(fr.get("evidence"), list), "fusion_report.evidence is a list")
print(f"         prism_score      = {fr.get('prism_score')}")
print(f"         verdict          = {fr.get('verdict', '')[:80]}")

# ---------------------------------------------------------------------------
# Step 5 – run a second time to build history
# ---------------------------------------------------------------------------
_section("Step 5 · Run engines a second time (builds history)")
r2 = requests.post(
    f"{BASE}/api/analysis/run-engines",
    params={"item_id": item_id},
    timeout=TIMEOUT,
)
check(r2.status_code == 201, f"Second POST /api/analysis/run-engines → {r2.status_code}")
run_resp2: dict[str, Any] = r2.json()
er2 = run_resp2["engine_run"]
check(er2["id"] != er["id"], f"Second run has a different EngineRun id ({er2['id']} ≠ {er['id']})")

# ---------------------------------------------------------------------------
# Step 6 – GET /api/analysis/engine-runs/{item_id}
# ---------------------------------------------------------------------------
_section("Step 6 · GET /api/analysis/engine-runs/{item_id}")
r = requests.get(f"{BASE}/api/analysis/engine-runs/{item_id}", timeout=TIMEOUT)
check(r.status_code == 200, f"GET engine-runs → {r.status_code}")
stored_runs: list[dict] = r.json()
check(isinstance(stored_runs, list), "Response is a list")
check(len(stored_runs) >= 2, f"At least 2 stored runs (got {len(stored_runs)})")
ids = [x["id"] for x in stored_runs]
check(er2["id"] in ids, "Second run's id present in response")
check(er["id"] in ids, "First run's id present in response")
print(f"         stored run ids   = {ids[:5]}")

# ---------------------------------------------------------------------------
# Step 7 – GET /api/analysis/fusion-history/{item_id}
# ---------------------------------------------------------------------------
_section("Step 7 · GET /api/analysis/fusion-history/{item_id}")
r = requests.get(f"{BASE}/api/analysis/fusion-history/{item_id}", timeout=TIMEOUT)
check(r.status_code == 200, f"GET fusion-history → {r.status_code}")
fusion_hist: list[dict] = r.json()
check(isinstance(fusion_hist, list), "Response is a list")
check(len(fusion_hist) >= 2, f"At least 2 fusion records (got {len(fusion_hist)})")
for rec in fusion_hist:
    check("prism_score" in rec, f"Record {rec.get('id')} has prism_score")
    check("verdict" in rec, f"Record {rec.get('id')} has verdict")

# ---------------------------------------------------------------------------
# Step 8 – existing /api/analysis/fusion-reports/{item_id} still works
# ---------------------------------------------------------------------------
_section("Step 8 · Dynamic /fusion-reports/{item_id} shape unchanged")
r = requests.get(f"{BASE}/api/analysis/fusion-reports/{item_id}", timeout=TIMEOUT)
check(r.status_code == 200, f"GET /fusion-reports/{{item_id}} → {r.status_code}")
dyn: dict[str, Any] = r.json()
required_fields = (
    "item_id", "prism_score", "novelty_score", "trust_score",
    "controversy_score", "adoption_gap_score", "transferability_score",
    "verdict", "evidence",
)
for field in required_fields:
    check(field in dyn, f"Dynamic response has field '{field}'")
check(dyn["item_id"] == item_id, "item_id matches in dynamic response")
print(f"         dynamic prism    = {dyn.get('prism_score')}")

# ---------------------------------------------------------------------------
# Step 9 – existing /api/analysis/fusion-reports list still works
# ---------------------------------------------------------------------------
_section("Step 9 · Dynamic /fusion-reports list endpoint still works")
r = requests.get(f"{BASE}/api/analysis/fusion-reports", params={"limit": 5}, timeout=TIMEOUT)
check(r.status_code == 200, f"GET /fusion-reports → {r.status_code}")
lst: list[dict] = r.json()
check(isinstance(lst, list), "Response is a list")
if lst:
    for field in required_fields:
        check(field in lst[0], f"List item has field '{field}'")
print(f"         list length      = {len(lst)}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{BOLD}{GREEN}All checks passed [OK]{RESET}\n")
