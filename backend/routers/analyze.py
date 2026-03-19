from datetime import datetime
import json
import logging
import uuid
import os
import asyncio
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Security, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter

from modules.decision_engine import generate_audit_trail, make_decision
from modules.feature_store import list_analyses, load_features, save_features, save_full_analysis, load_full_analysis
from modules.ingestion import (
    compute_financial_ratios,
    fetch_gst_from_databricks,
    parse_bank_statement_csv,
    parse_bureau_json,
    parse_financial_pdf,
    reconcile_gst_with_bank,
)
from modules.ml_engine import (
    compute_risk_premium,
    get_model_metrics,
    get_shap_explanation,
    load_models,
    predict_limit,
    predict_pd,
)
from modules.risk_synthesis import compute_capital_impact, compute_composite_risk
from modules.stress_test import run_stress_test
from modules.web_research import simulate_web_research

router = APIRouter()

# ── Feature 1: SSE Real-Time Progress ────────────────────
ANALYSIS_PROGRESS_EVENTS: Dict[str, asyncio.Queue] = {}

async def _emit_progress(analysis_id: str, message: str, step: int, status: str = "processing"):
    """Helper to push messages to anyone listening on the SSE endpoint"""
    queue = ANALYSIS_PROGRESS_EVENTS.get(analysis_id)
    if queue:
        payload = json.dumps({"step": step, "message": message, "status": status})
        await queue.put(f"data: {payload}\n\n")

# ── Feature 2: Persistent Datastore (replacing in-memory dict) ──
import aiofiles

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sessions.json")

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

ANALYSIS_DB = _load_db()

security = HTTPBearer(auto_error=False)

try:
    API_KEYS = json.loads(os.environ.get("TENANT_API_KEYS", "{}"))
except json.JSONDecodeError:
    API_KEYS = {}


from security.auth import verify_firebase_token

async def get_tenant(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Dependency to extract and validate B2B tenant from API Key or Firebase Auth."""
    if not credentials:
        return {"tenant_id": "tnt_b2c_individual", "tier": "free", "webhook_url": None}

    token = credentials.credentials
    tenant = API_KEYS.get(token)
    
    if tenant:
        return tenant
        
    # If not a static API key, attempt to verify as a Firebase JWT
    try:
        decoded_token = verify_firebase_token(credentials)
        return {
            "tenant_id": decoded_token.get("uid", "firebase_user"),
            "tier": "enterprise",
            "webhook_url": None
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Authentication Token")


async def dispatch_webhook(webhook_url: str, analysis_id: str, decision: str, limit: float):
    """Asynchronously dispatch completion payload to B2B institutional client."""
    if not webhook_url:
        return

    payload = {
        "event": "cam_generation.completed",
        "analysis_id": analysis_id,
        "decision": decision,
        "approved_limit": limit,
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
            logging.info("Webhook dispatched to %s for analysis %s", webhook_url, analysis_id)
    except Exception as exc:
        logging.error("Webhook dispatch failed for %s: %s", analysis_id, exc)


class CustomerDetails(BaseModel):
    name: str = ""
    id: str = ""
    industry: str = "Manufacturing"
    constitution: str = ""
    gstin: str = ""
    cin: str = ""
    pan: str = ""


class FinancialDetails(BaseModel):
    operating_income: float = 0
    non_operating_income: float = 0
    short_term_liab: float = 0
    long_term_liab: float = 0
    contingent_liab: float = 0
    internal_rating: str = ""
    external_rating: str = ""
    bureau_score: int = 700
    current_assets: float = 0
    fixed_assets: float = 0
    intangible_assets: float = 0


class FacilityDetails(BaseModel):
    amount: float = 0
    currency: str = "INR"
    purpose: str = ""
    term_months: int = 12
    repayment_method: str = "EMI"


class WriteupDetails(BaseModel):
    swot: str = ""
    business_overview: str = ""
    policy_exceptions: str = ""


class ExposureDetails(BaseModel):
    internal: float = 0
    external: float = 0
    parent_child: float = 0
    geography: str = "Low"
    industry: str = "Medium"
    entity: str = "Low"


class ApprovalStatus(BaseModel):
    risk_dept: str = "Pending"
    legal_dept: str = "Pending"
    compliance: str = "Pending"


class AnalyzeRequest(BaseModel):
    analysis_id: str
    customer: CustomerDetails
    financials: FinancialDetails
    facility: FacilityDetails
    collateral_list: List[dict] = []
    writeup: WriteupDetails
    kyc_status: str = "Pending"
    exposure: ExposureDetails
    approval: ApprovalStatus
    remarks: List[str] = []


def _ensure_session(tenant_id: str, analysis_id: str, status: str = "INITIATED") -> Dict[str, Any]:
    db = _load_db()
    tenant_db = db.setdefault(tenant_id, {})
    session = tenant_db.setdefault(analysis_id, {"raw_extracts": {}, "status": status})
    session.setdefault("raw_extracts", {})
    session.setdefault("status", status)
    _save_db(db)
    
    # Keep the global in sync just in case
    global ANALYSIS_DB
    ANALYSIS_DB = db
    
    return session


def _build_financial_payload(req: AnalyzeRequest, session: Dict[str, Any]) -> Dict[str, Any]:
    uploaded_financials = session.get("raw_extracts", {}).get("financial_pdf", {})
    
    # Calculate net_income properly from payload rather than magic 12%
    # Try to extract it from writeup or financials if provided, else use rough industry default of 5%
    default_net_income = req.financials.operating_income * 0.05 if req.financials.operating_income else 0
    calculated_net_income = req.financials.non_operating_income if req.financials.non_operating_income else default_net_income

    manual_financials = {
        "revenue": req.financials.operating_income,
        "net_income": calculated_net_income,
        "total_assets": req.financials.current_assets + req.financials.fixed_assets + req.financials.intangible_assets,
        "total_liabilities": req.financials.short_term_liab + req.financials.long_term_liab + req.financials.contingent_liab,
        "total_debt": req.financials.long_term_liab,
        "current_assets": req.financials.current_assets,
        "current_liabilities": req.financials.short_term_liab,
        "short_term_liab": req.financials.short_term_liab,
        "long_term_liab": req.financials.long_term_liab,
        "contingent_liab": req.financials.contingent_liab,
    }
    manual_financials["total_equity"] = max(manual_financials["total_assets"] - manual_financials["total_liabilities"], 0)

    merged = dict(manual_financials)
    for key, value in uploaded_financials.items():
        if value not in (None, "", [], {}):
            merged[key] = value

    if not merged.get("total_equity") and merged.get("total_assets") is not None and merged.get("total_liabilities") is not None:
        merged["total_equity"] = max(float(merged["total_assets"]) - float(merged["total_liabilities"]), 0)
    return merged


def _dump_model(model: BaseModel) -> Dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    analysis_id: Optional[str] = Form(None),
    tenant: Dict = Depends(get_tenant),
):
    """Upload and parse a document, returning a temporary analysis_id."""
    filename = getattr(file, "filename", "") or ""
    if not filename.lower().endswith((".pdf", ".csv")):
        raise HTTPException(status_code=400, detail={"error": "Unsupported file type. Strictly .pdf and .csv are allowed."})

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail={"error": "File size exceeds 50MB limit."})

    analysis_id = analysis_id or str(uuid.uuid4())
    tenant_id = tenant["tenant_id"]

    if doc_type == "financial_pdf":
        extracted = parse_financial_pdf(content)
    elif doc_type == "bank_csv":
        extracted = parse_bank_statement_csv(content)
    elif doc_type == "bureau_json":
        try:
            extracted = parse_bureau_json(json.loads(content.decode("utf-8")))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid bureau JSON: {exc}") from exc
    else:
        raise HTTPException(status_code=400, detail="Invalid doc_type")

    db = _load_db()
    session = _ensure_session(tenant_id, analysis_id, status="UPLOADED")
    
    # Load latest to ensure we overwrite correctly
    db = _load_db()
    db[tenant_id][analysis_id]["raw_extracts"][doc_type] = extracted
    db[tenant_id][analysis_id]["status"] = "UPLOADED"
    _save_db(db)

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "message": f"Successfully parsed and stored {file.filename} in datastore",
        "extracted_data": extracted,
    }


from services.external_aggregator import ExternalDataAggregator

@router.post("/analyze", status_code=202, dependencies=[Depends(RateLimiter(times=5, minutes=1))])
async def run_full_analysis(
    req: AnalyzeRequest,
    tenant: Dict = Depends(get_tenant),
):
    """Run the complete end-to-end credit decisioning pipeline via Celery async workers."""
    
    tenant_id = tenant["tenant_id"]
    session = _ensure_session(tenant_id, req.analysis_id, status="INITIATED_VIA_LOS")

    financials = _build_financial_payload(req, session)
    total_collateral_value = sum(float(item.get("value", 0) or 0) for item in req.collateral_list)

    # Convert the pydantic model to a standard dict for JSON serialization over Celery
    req_payload = _dump_model(req)
    webhook_url = tenant.get("webhook_url")

    # Queue the Background job instead of blocking!
    from tasks import process_analysis_task
    process_analysis_task.delay(req_payload, tenant_id, webhook_url, financials, total_collateral_value)

    return {
        "status": "processing",
        "analysis_id": req.analysis_id,
        "message": "Analysis queued for background processing immediately.",
    }


@router.get("/analyses")
async def get_all_analyses():
    """List all past analyses (from feature store)."""
    return {"analyses": list_analyses()}


@router.get("/metrics")
@cache(expire=60)
async def get_system_metrics():
    """Return model performance and bias metrics for the dashboard."""
    return get_model_metrics()


@router.post("/drafts/save")
async def save_los_draft(req: AnalyzeRequest, tenant: Dict = Depends(get_tenant)):
    """Save an in-progress Credit Proposal Draft to the tenant datastore."""
    session = _ensure_session(tenant["tenant_id"], req.analysis_id, status="DRAFT")
    
    db = _load_db()
    db[tenant["tenant_id"]][req.analysis_id]["draft_payload"] = _dump_model(req)
    db[tenant["tenant_id"]][req.analysis_id]["status"] = "DRAFT"
    _save_db(db)
    
    return {"status": "success", "message": "Draft saved securely.", "analysis_id": req.analysis_id}


@router.get("/drafts/load/{analysis_id}")
async def load_los_draft(analysis_id: str, tenant: Dict = Depends(get_tenant)):
    """Load an in-progress Credit Proposal Draft."""
    db = _load_db()
    session = db.get(tenant["tenant_id"], {}).get(analysis_id)
    if not session or "draft_payload" not in session:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "success", "draft": session["draft_payload"]}


@router.get("/drafts/all")
async def get_all_drafts(tenant: Dict = Depends(get_tenant)):
    """Return all drafts for the specific tenant."""
    drafts_list = []
    db = _load_db()
    for analysis_id, session_data in db.get(tenant["tenant_id"], {}).items():
        if session_data.get("status") == "DRAFT":
            draft_payload = session_data.get("draft_payload", {})
            drafts_list.append(
                {
                    "analysis_id": analysis_id,
                    "company_name": draft_payload.get("customer", {}).get("name", "Unnamed Draft"),
                    "status": "DRAFT",
                    "limit_recommendation": draft_payload.get("facility", {}).get("amount", 0),
                }
            )
    return {"drafts": drafts_list}


@router.get("/progress/{analysis_id}")
async def analysis_progress(analysis_id: str):
    """Server-Sent Events (SSE) endpoint to stream analysis progression."""
    if analysis_id not in ANALYSIS_PROGRESS_EVENTS:
        ANALYSIS_PROGRESS_EVENTS[analysis_id] = asyncio.Queue()

    async def event_generator():
        queue = ANALYSIS_PROGRESS_EVENTS[analysis_id]
        try:
            while True:
                message = await queue.get()
                yield message
                if "completed" in message or "error" in message:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if analysis_id in ANALYSIS_PROGRESS_EVENTS:
                del ANALYSIS_PROGRESS_EVENTS[analysis_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")
