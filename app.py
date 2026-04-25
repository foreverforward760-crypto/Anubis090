"""
ANUBIS v5.0.0 — LUMINARK Portfolio Intelligence Platform
Powered by LuminarkHybridEngine v8.2.0 (Tumbling Inversion Principle)
Author: Richard Stanfield, MAAT
"""

import os
import sys
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# --- Engine Integration ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "luminark-engine"))
from luminark import EngineFactory, NSDTBuilder, SAPStage
from luminark.sap_types import SystemState

# --- Configuration ---
API_KEY      = os.getenv("ANUBIS_API_KEY",     "demo-key-change-me")
DEMO_KEY     = os.getenv("ANUBIS_DEMO_KEY",    "demo-public")
ENGINE_PRESET = os.getenv("ANUBIS_ENGINE_PRESET", "industrial_strict")
DB_PATH      = os.getenv("ANUBIS_DB_PATH",     "anubis_audit.db")

# Initialize engine once at startup
engine = EngineFactory.create(preset=ENGINE_PRESET)

# --- FastAPI App ---
app = FastAPI(
    title="ANUBIS — LUMINARK Portfolio Intelligence",
    version="5.0.0",
    description=(
        "SAP 10-stage classification, Stage 5 bifurcation, "
        "NMAP economic classifier, 369 resonance, compliance overwatch."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


# --- Auth Dependency ---
def verify_api_key(x_anubis_api_key: Optional[str] = Header(None)):
    if x_anubis_api_key not in (API_KEY, DEMO_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_anubis_api_key


# --- SQLite Audit ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit (
                id            TEXT PRIMARY KEY,
                timestamp     TEXT,
                endpoint      TEXT,
                api_key       TEXT,
                request       JSON,
                response      JSON,
                sap_stage     INTEGER,
                is_trap       BOOLEAN,
                unified_field REAL
            )
        """)


init_db()


def log_audit(
    endpoint: str,
    api_key: str,
    request: Dict,
    response: Dict,
    state: Optional[SystemState] = None,
):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT INTO audit
                   (id, timestamp, endpoint, api_key, request, response,
                    sap_stage, is_trap, unified_field)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    datetime.utcnow().isoformat(),
                    endpoint,
                    api_key[:8] + "..." if api_key else "anonymous",
                    str(request),
                    str(response),
                    state.stage.value          if state else None,
                    state.is_trap              if state else None,
                    state.unified_field_value  if state else None,
                ),
            )
    except Exception:
        pass  # Non-blocking audit — never crash the request


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    complexity:   float = Field(..., ge=0, le=100, description="Volatility / route entropy")
    stability:    float = Field(..., ge=0, le=100, description="HOS remaining %")
    tension:      float = Field(..., ge=0, le=100, description="Recovery debt")
    adaptability: float = Field(..., ge=0, le=100, description="Communication coherence")
    coherence:    float = Field(..., ge=0, le=100, description="MAAT score")
    system_id:    Optional[str] = None


class ClassifyResponse(BaseModel):
    stage:                    int
    stage_name:               str
    is_trap:                  bool
    trap_reason:              Optional[str]
    recommended_action:       str
    unified_field:            float
    yield_score:              float
    recalibration_recommended: bool
    recalibration_reason:     Optional[str]


class BifurcationRequest(BaseModel):
    gate:       int   = Field(..., ge=0, le=9)
    micro_stage: float = Field(0.5, ge=0, le=1)
    energy:     float = Field(..., ge=0, le=100)
    integrity:  float = Field(..., ge=0, le=100)
    maat:       float = Field(..., ge=0, le=100)
    system_id:  Optional[str] = None


class BifurcationResponse(BaseModel):
    advance_prob:    float
    regression_prob: float
    crisis_prob:     float
    recommended_path: str
    unified_field:   float
    stage_after:     int


class NMAPRequest(BaseModel):
    gdp_growth:          float
    unemployment:        float
    inflation:           float
    debt_to_gdp:         float
    asset_deviation_sd:  float
    credit_expansion:    float


class NMAPResponse(BaseModel):
    economic_stage:    int
    stage_name:        str
    is_trap:           bool
    trap_indicators:   List[str]
    recommended_action: str


class FrequencyRequest(BaseModel):
    dominant_freq_hz:   float = 432.0
    harmonic_alignment: float = 0.5
    amplitude_variance: float = 0.5
    signal_to_noise_db: float = 20.0
    system_id:          Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Core Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest, api_key: str = Depends(verify_api_key)):
    """Full SAP stage classification with trap detection and unified field."""
    nsdt  = NSDTBuilder.from_generic(request.dict(exclude={"system_id"}))
    state = engine.analyze(nsdt, system_id=request.system_id or "anubis-session")

    response = {
        "stage":                    state.stage.value,
        "stage_name":               state.stage.name,
        "is_trap":                  state.is_trap,
        "trap_reason":              state.trap_reason,
        "recommended_action":       state.recommended_action,
        "unified_field":            state.unified_field_value,
        "yield_score":              max(0.0, 100.0 - state.unified_field_value * 20),
        "recalibration_recommended": state.recalibration_recommended,
        "recalibration_reason":     state.recalibration_reason,
    }
    log_audit("/api/classify", api_key, request.dict(), response, state)
    return response


@app.post("/api/sar/bifurcation", response_model=BifurcationResponse)
async def sar_bifurcation(
    request: BifurcationRequest, api_key: str = Depends(verify_api_key)
):
    """Stage 5 three-way probability using unified field and recalibration logic."""
    from luminark import RecalibrationEngine
    from luminark.sap_types import NSDTVector

    nsdt = NSDTVector(
        complexity=request.energy * 0.5,
        stability=request.integrity,
        tension=100 - request.maat,
        adaptability=request.maat,
        coherence=request.maat * 0.8,
    )
    state = SystemState(
        stage=SAPStage(request.gate),
        nsdt=nsdt,
        is_trap=False,
        recommended_action="",
        unified_field_value=0.0,
    )

    should_recal, reason = RecalibrationEngine.should_recalibrate(state)
    if should_recal:
        advance_prob    = 0.3
        regression_prob = 0.6
        crisis_prob     = 0.1
        recommended     = "GRACEFUL_REGRESSION"
        stage_after     = 4
    else:
        advance_prob    = 0.7
        regression_prob = 0.2
        crisis_prob     = 0.1
        recommended     = "ADVANCE"
        stage_after     = 6

    uf = engine.analyze(nsdt, system_id=request.system_id or "bifurcation").unified_field_value

    response = {
        "advance_prob":    advance_prob,
        "regression_prob": regression_prob,
        "crisis_prob":     crisis_prob,
        "recommended_path": recommended,
        "unified_field":   uf,
        "stage_after":     stage_after,
    }
    log_audit("/api/sar/bifurcation", api_key, request.dict(), response)
    return response


@app.post("/api/nmap/classify", response_model=NMAPResponse)
async def nmap_classify(request: NMAPRequest, api_key: str = Depends(verify_api_key)):
    """NMAP economic stage classifier using engine thresholds."""
    nsdt = NSDTBuilder.from_generic({
        "complexity":   min(100, request.credit_expansion),
        "stability":    max(0, 100 - request.asset_deviation_sd * 10),
        "tension":      min(100, request.inflation * 10 + request.debt_to_gdp / 2),
        "adaptability": max(0, 100 - abs(request.gdp_growth - 3)),
        "coherence":    max(0, 100 - request.unemployment * 5),
    })
    state = engine.analyze(nsdt, system_id="nmap-economy")

    response = {
        "economic_stage":   state.stage.value,
        "stage_name":       state.stage.name,
        "is_trap":          state.is_trap,
        "trap_indicators":  [state.trap_reason] if state.is_trap else [],
        "recommended_action": state.recommended_action,
    }
    log_audit("/api/nmap/classify", api_key, request.dict(), response, state)
    return response


@app.post("/api/frequency", response_model=ClassifyResponse)
async def frequency_analyze(
    request: FrequencyRequest, api_key: str = Depends(verify_api_key)
):
    """Bio-resonance / acoustic frequency analysis via FrequencyAdapter."""
    from luminark import FrequencyAdapter

    nsdt  = FrequencyAdapter.from_frequency_metrics(request.dict(exclude={"system_id"}))
    state = engine.analyze(nsdt, system_id=request.system_id or "freq-session")

    response = {
        "stage":                    state.stage.value,
        "stage_name":               state.stage.name,
        "is_trap":                  state.is_trap,
        "trap_reason":              state.trap_reason,
        "recommended_action":       state.recommended_action,
        "unified_field":            state.unified_field_value,
        "yield_score":              max(0.0, 100.0 - state.unified_field_value * 20),
        "recalibration_recommended": state.recalibration_recommended,
        "recalibration_reason":     state.recalibration_reason,
    }
    log_audit("/api/frequency", api_key, request.dict(), response, state)
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Utility Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "operational", "engine": ENGINE_PRESET, "version": "5.0.0"}


@app.get("/api/sar/stage_names")
async def stage_names():
    """Return all canonical SAP stage names — non-negotiable constants."""
    return {s.value: s.name for s in SAPStage}


@app.get("/api/audit/recent")
async def recent_audit(limit: int = 20, api_key: str = Depends(verify_api_key)):
    """Return the most recent audit log entries."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, timestamp, endpoint, sap_stage, is_trap, unified_field "
            "FROM audit ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": r[0], "timestamp": r[1], "endpoint": r[2],
            "sap_stage": r[3], "is_trap": bool(r[4]), "unified_field": r[5],
        }
        for r in rows
    ]
