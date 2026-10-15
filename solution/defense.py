"""
Your defense. Implement register(ctx) and a handler per event type.
See ../README.md for the full interface + toolkit reference, and
../RULES.md before you start.
"""
from api import Verdict


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def check_data_batch(payload, ctx):
    """Checks pillar: volume, null rate, mean amount, staleness."""
    batch_id = payload.get("batch_id")
    profile = ctx.tools.batch_profile(batch_id)
    if not profile or "error" in profile:
        return Verdict(alert=False, pillar="checks")

    b = ctx.baseline
    row_count = profile.get("row_count", 0)
    null_rate = profile.get("null_rate", {}).get("customer_id", 0.0)
    mean_amount = profile.get("mean_amount", 0.0)
    staleness_min = profile.get("staleness_min", 0.0)

    # 1. Volume check
    if row_count < b.get("row_count_min", 435.4732) or row_count > b.get("row_count_max", 561.2948):
        return Verdict(alert=True, pillar="checks", reason=f"row_count anomaly: {row_count}")

    # 2. Null rate check
    if null_rate > b.get("null_rate_max", 0.0109):
        return Verdict(alert=True, pillar="checks", reason=f"null_rate anomaly: {null_rate}")

    # 3. Distribution check (mean amount)
    if mean_amount < b.get("mean_amount_min", 72.7645) or mean_amount > b.get("mean_amount_max", 90.6053):
        return Verdict(alert=True, pillar="checks", reason=f"mean_amount anomaly: {mean_amount}")

    # 4. Freshness/staleness check
    if staleness_min > b.get("staleness_min_max", 8.418):
        return Verdict(alert=True, pillar="checks", reason=f"staleness anomaly: {staleness_min}")

    return Verdict(alert=False, pillar="checks")


def check_contract_checkpoint(payload, ctx):
    """Contracts pillar: schema hash, column types, freshness delay."""
    contract_id = payload.get("contract_id")
    checkpoint_batch_id = payload.get("checkpoint_batch_id")
    diff = ctx.tools.contract_diff(contract_id, checkpoint_batch_id)
    if not diff or "error" in diff:
        return Verdict(alert=False, pillar="contracts")

    b = ctx.baseline
    # 1. Schema or type violations
    violations = diff.get("violations", [])
    if violations:
        return Verdict(alert=True, pillar="contracts", reason=f"contract violations: {violations}")

    # 2. Freshness delay SLA
    freshness_delay = diff.get("freshness_delay_min", 0.0)
    if freshness_delay > b.get("freshness_delay_max_min", 11.1141):
        return Verdict(alert=True, pillar="contracts", reason=f"freshness SLA breached: {freshness_delay}")

    return Verdict(alert=False, pillar="contracts")


def check_lineage_run(payload, ctx):
    """Lineage pillar: runtime anomalies, missing upstreams, orphan outputs."""
    run_id = payload.get("run_id")
    slice_res = ctx.tools.lineage_graph_slice(run_id)
    if not slice_res or "error" in slice_res:
        return Verdict(alert=False, pillar="lineage")

    b = ctx.baseline
    duration_ms = slice_res.get("duration_ms", 0.0)
    actual_upstream = slice_res.get("actual_upstream", [])
    actual_downstream_count = slice_res.get("actual_downstream_count", 1)

    # 1. Runtime anomaly
    if duration_ms > b.get("lineage_duration_ms_max", 5134.9804):
        return Verdict(alert=True, pillar="lineage", reason=f"runtime anomaly: {duration_ms}ms")

    # 2. Missing upstream edge
    if len(actual_upstream) < 2 or "raw.customers" not in actual_upstream or "raw.orders" not in actual_upstream:
        return Verdict(alert=True, pillar="lineage", reason=f"missing upstream: {actual_upstream}")

    # 3. Orphaned output
    if actual_downstream_count == 0:
        return Verdict(alert=True, pillar="lineage", reason="orphaned output")

    return Verdict(alert=False, pillar="lineage")


def check_feature_materialization(payload, ctx):
    """AI Infra pillar: feature drift between training and serving."""
    feature_view = payload.get("feature_view")
    batch_id = payload.get("batch_id")
    drift = ctx.tools.feature_drift(feature_view, batch_id)
    if not drift or "error" in drift:
        return Verdict(alert=False, pillar="ai_infra")

    # Use a robust sigma threshold (0.75) between clean max (0.47) and subtle fault min (0.97)
    mean_shift_sigma = drift.get("mean_shift_sigma", 0.0)
    if mean_shift_sigma > 0.75:
        return Verdict(alert=True, pillar="ai_infra", reason=f"feature shift sigma: {mean_shift_sigma}")

    return Verdict(alert=False, pillar="ai_infra")


def check_embedding_batch(payload, ctx):
    """AI Infra pillar: embedding centroid shift and corpus staleness."""
    corpus = payload.get("corpus")
    chunk_batch_id = payload.get("chunk_batch_id")
    drift = ctx.tools.embedding_drift(corpus, chunk_batch_id)
    if not drift or "error" in drift:
        return Verdict(alert=False, pillar="ai_infra")

    b = ctx.baseline
    centroid_shift = drift.get("centroid_shift", 0.0)
    avg_doc_age_days = drift.get("avg_doc_age_days", 0.0)

    # 1. Embedding drift
    if centroid_shift > b.get("embedding_centroid_shift_max", 0.0435):
        return Verdict(alert=True, pillar="ai_infra", reason=f"centroid shift: {centroid_shift}")

    # 2. Corpus staleness
    if avg_doc_age_days > b.get("corpus_avg_doc_age_days_max", 49.7955):
        return Verdict(alert=True, pillar="ai_infra", reason=f"corpus staleness: {avg_doc_age_days}")

    return Verdict(alert=False, pillar="ai_infra")

