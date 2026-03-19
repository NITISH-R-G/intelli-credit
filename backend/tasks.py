import logging
import asyncio
from typing import Dict, Any

from celery_worker import celery_app
from modules.decision_engine import generate_audit_trail, make_decision
from modules.feature_store import save_features, save_full_analysis
from modules.ingestion import compute_financial_ratios, fetch_gst_from_databricks, reconcile_gst_with_bank
from modules.ml_engine import compute_risk_premium, get_model_metrics, get_shap_explanation, load_models, predict_limit, predict_pd
from modules.risk_synthesis import compute_capital_impact, compute_composite_risk
from modules.stress_test import run_stress_test
from modules.web_research import simulate_web_research
try:
    from services.external_aggregator import ExternalDataAggregator
except ImportError:
    pass

from modules.pii_masker import PIIMasker

import httpx
from datetime import datetime

import os
import json

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sessions.json")

def _load_db() -> dict:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_db(db_data: dict):
    with open(DB_FILE, "w") as f:
        json.dump(db_data, f, indent=2)

def set_progress(tenant_id: str, analysis_id: str, status: str):
    db = _load_db()
    if tenant_id in db and analysis_id in db[tenant_id]:
        db[tenant_id][analysis_id]["status"] = status
        _save_db(db)

def dispatch_webhook(webhook_url: str, analysis_id: str, decision: str, limit: float):
    payload = {
        "event": "cam_generation.completed",
        "analysis_id": analysis_id,
        "decision": decision,
        "approved_limit": limit,
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        import requests
        requests.post(webhook_url, json=payload, timeout=5.0)
    except Exception as exc:
        logging.error("Webhook dispatch failed for %s: %s", analysis_id, exc)

@celery_app.task(name="tasks.process_analysis_task")
def process_analysis_task(req_dict: Dict[str, Any], tenant_id: str, webhook_url: str, financials: Dict[str, Any], total_collateral_value: float):
    return asyncio.run(_async_process_analysis(req_dict, tenant_id, webhook_url, financials, total_collateral_value))

async def _async_process_analysis(req_dict: Dict[str, Any], tenant_id: str, webhook_url: str, financials: Dict[str, Any], total_collateral_value: float):
    analysis_id = req_dict["analysis_id"]
    try:
        load_models()
    except Exception as exc:
        logging.warning(f"Warning: models not available for eager load. {exc}")

    set_progress(tenant_id, analysis_id, "Processing: Initializing features")

    db = _load_db()
    session = db.get(tenant_id, {}).get(analysis_id, {})
    bank_data = session.get("raw_extracts", {}).get("bank_csv", {})
    bureau_data = session.get("raw_extracts", {}).get("bureau_json", {"bureau_score": req_dict["financials"]["bureau_score"]})

    features = compute_financial_ratios(
        financials=financials,
        bank_data=bank_data,
        bureau_data=bureau_data,
        collateral_value=total_collateral_value,
        loan_amount=req_dict["facility"]["amount"],
    )

    gst_data = fetch_gst_from_databricks(str(analysis_id))
    gst_bank_metrics = reconcile_gst_with_bank(gst_data, bank_data)
    features.update(gst_data)
    features.update(gst_bank_metrics)

    set_progress(tenant_id, analysis_id, "Processing: Fetching APIs")

    try:
        aggregator = ExternalDataAggregator()
        gstin = req_dict["customer"]["gstin"] or (f"27{req_dict['customer']['id']}1Z5"[:15] if req_dict["customer"]["id"] else "27AAACA1234A1Z5")
        cin = req_dict["customer"]["cin"] or (f"U74999MH2023PTC{req_dict['customer']['id']}"[:21] if req_dict["customer"]["id"] else "U74999MH2023PTC123456")
        pan = req_dict["customer"]["pan"] or (f"ABCDE{req_dict['customer']['id']}F"[:10] if req_dict["customer"]["id"] else "ABCDE1234F")

        ext_data = await aggregator.aggregate_borrower_facts(
            company_name=req_dict["customer"]["name"],
            company_id=req_dict["customer"]["id"],
            gstin=gstin,
            cin=cin,
            pan=pan
        )
        features.update(ext_data)
    except NameError:
        ext_data = {}

    features["company_name"] = req_dict["customer"]["name"]
    features["industry"] = req_dict["customer"]["industry"]
    features["existing_exposure"] = req_dict["exposure"]["internal"] + req_dict["exposure"]["external"] + req_dict["exposure"]["parent_child"]

    real_vintage = ext_data.get("cibil_credit_history_months", 0)
    vintage_months = real_vintage if real_vintage > 0 else float(bureau_data.get("credit_history_months", 60) or 60)
    features["years_in_business"] = max(1.0, round(vintage_months / 12.0, 1))

    if ext_data.get("cibil_commercial_score", -1) > 0:
        cmr = ext_data["cibil_commercial_score"]
        if cmr <= 10:
            features["bureau_score"] = int(900 - (cmr - 1) * (600 / 9))
        else:
            features["bureau_score"] = cmr

    set_progress(tenant_id, analysis_id, "Processing: Web Research")
    
    # PII Masking applied before external LLM interaction
    masked_overview = PIIMasker.mask_text(req_dict["writeup"]["business_overview"])
    masked_swot = PIIMasker.mask_text(req_dict["writeup"]["swot"])

    web_research_data = await simulate_web_research(
        company_name=req_dict["customer"]["name"],
        industry=req_dict["customer"]["industry"],
        revenue=features.get("revenue", 0),
        bureau_score=features.get("bureau_score", 700),
        site_visit_insights=masked_overview,
        management_interview_notes=masked_swot,
    )
    features["industry_risk"] = web_research_data.get("industry_macro", {}).get("risk_factor", 0.3)

    set_progress(tenant_id, analysis_id, "Processing: ML Inference")
    save_features(analysis_id, features)

    try:
        pd_score, _ = predict_pd(features)
        recommended_limit = predict_limit(features)
        shap_explanation = get_shap_explanation(features)
        model_metrics = get_model_metrics()
    except Exception as exc:
        logging.error(f"ML inference fallback engaged: {exc}")
        pd_score = 0.15
        recommended_limit = req_dict["facility"]["amount"] * 0.8
        shap_explanation = {"top_5_factors": []}
        model_metrics = {}

    primary_insight_bps = web_research_data.get("primary_insights", {}).get("impact_bps", 0)
    risk_premium = compute_risk_premium(
        pd_score=pd_score,
        industry_risk=features.get("industry_risk", 0.3),
        collateral_coverage=features.get("collateral_coverage", 1.0),
    )
    if req_dict["writeup"]["policy_exceptions"]:
        primary_insight_bps += 100
    risk_premium["total_rate_bps"] += primary_insight_bps
    risk_premium["total_rate"] = risk_premium["total_rate_bps"] / 10000.0

    stress_results = run_stress_test(features, pd_score)
    composite_risk = compute_composite_risk(pd_score, features, web_research_data, stress_results)
    exposure_penalty = 15 if req_dict["exposure"]["industry"] == "High" or req_dict["exposure"]["geography"] == "High" else 0
    composite_risk["composite_score"] = min(100, composite_risk.get("composite_score", 50) + exposure_penalty)

    capital_impact = compute_capital_impact(
        loan_amount=req_dict["facility"]["amount"],
        pd_score=pd_score,
        composite_score=composite_risk.get("composite_score", 50),
    )

    set_progress(tenant_id, analysis_id, "Processing: Synthesizing Decision")
    decision_result = make_decision(
        pd_score=pd_score,
        composite_risk=composite_risk,
        web_research=web_research_data,
        features=features,
        shap_explanation=shap_explanation,
        recommended_limit=recommended_limit,
        risk_premium=risk_premium,
    )
    
    decision_result["company_summary"] = web_research_data.get("company_profile", "")

    from modules.llm_five_c_analyzer import synthesize_five_cs
    decision_result["five_c_synthesis"] = synthesize_five_cs(features, web_research_data)

    audit_trail = generate_audit_trail(
        analysis_id=analysis_id,
        company_name=req_dict["customer"]["name"],
        industry=req_dict["customer"]["industry"],
        decision_result=decision_result,
        features=features,
        web_research=web_research_data,
        stress_test=stress_results,
    )

    full_result = {
        "analysis_id": analysis_id,
        "company_name": req_dict["customer"]["name"],
        "industry": req_dict["customer"]["industry"],
        "decision": decision_result,
        "features": features,
        "web_research": web_research_data,
        "stress_test": stress_results,
        "composite_risk": composite_risk,
        "risk_premium": risk_premium,
        "capital_impact": capital_impact,
        "shap_explanation": shap_explanation,
        "audit_trail": audit_trail,
        "model_metrics": model_metrics,
        "workflow_state": req_dict["approval"],
    }

    db = _load_db()
    if tenant_id in db and analysis_id in db[tenant_id]:
        db[tenant_id][analysis_id]["full_result"] = full_result
        db[tenant_id][analysis_id]["status"] = "COMPLETED"
        _save_db(db)

    save_full_analysis(analysis_id, full_result)

    if webhook_url:
        dispatch_webhook(
            webhook_url,
            analysis_id,
            decision_result.get("decision", "PENDING"),
            decision_result.get("summary", {}).get("recommended_limit", 0),
        )

    return full_result
