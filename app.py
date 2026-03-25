"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ANUBIS — LUMINARK Portfolio Intelligence & Compliance Platform              ║
║  Version 3.0.0  |  Production Licensed Software                             ║
║                                                                              ║
║  Copyright © 2024-2026 Richard L. Stanfield                                 ║
║  Meridian Axiom Alignment Technologies (MAAT)                               ║
║  All Rights Reserved.                                                        ║
║                                                                              ║
║  PROPRIETARY AND CONFIDENTIAL                                                ║
║  This software and the SAP/NSDT methodology contained herein are the        ║
║  exclusive intellectual property of Richard L. Stanfield and MAAT.          ║
║  Patent Pending — USPTO (Application filed March 2026)                      ║
║                                                                              ║
║  UNAUTHORIZED COPYING, DISTRIBUTION, MODIFICATION, OR USE OF THIS           ║
║  SOFTWARE, VIA ANY MEDIUM, IS STRICTLY PROHIBITED WITHOUT A VALID           ║
║  COMMERCIAL LICENSE AGREEMENT FROM RICHARD L. STANFIELD / MAAT.            ║
║                                                                              ║
║  Licensed use is governed by the ANUBIS Commercial License Agreement.       ║
║  Contact: info.rstanfield@gmail.com                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

ANUBIS Capabilities:
  • SAP 10-stage portfolio and holding classification (NSDT framework)
  • Real-time stock data via yfinance (falls back to deterministic mock)
  • Position Trajectory Tracker: session-level stage_velocity, risk_momentum,
    rigidity_index, recovery_index across the full session
  • Discipline Protocol: HUBRIS_SCANNER + FALSE_BREAKOUT_DETECTION + CONTROLLED_EXPOSURE_REDUCTION
  • Drawdown Recovery Protocol: LAST_HEALTHY_BASELINE + BASELINE_RECOVERY_SEQUENCE + CIRCUIT_BREAKER_MODE
  • Adaptive Rebalancer: 60% reroute from Stage 0-2 holdings to healthy ones
  • Stop-Loss & Replace Protocol: position quarantine + regeneration suggestions
  • CITI: Systemic Tumbling Alert across portfolio + behavioral domains
  • Trader Behavior Profiler: 7-metric behavioral stage assessment
  • Compliance & Overwatch Layer: multi-platform rule enforcement + violation log
  • API Key authentication with tiered access control
  • SQLite persistence for compliance data, alerts, and audit trail
  • Serves the React frontend from /static/index.html
"""

from __future__ import annotations
import math, time, re, os, hashlib, json, sqlite3, secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_403_FORBIDDEN
from pydantic import BaseModel, Field

# ── Optional real-data dependency ─────────────────────────────────────────────
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
#  API KEY AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════
_API_KEY_NAME   = "X-ANUBIS-API-KEY"
_api_key_header = APIKeyHeader(name=_API_KEY_NAME, auto_error=False)

# Master key from environment; auto-generate a stable one if not set
_MASTER_KEY = os.getenv("ANUBIS_API_KEY") or None
_DEMO_KEY   = "ANUBIS-DEMO-" + hashlib.md5(b"anubis-demo-key-v3").hexdigest()[:12].upper()

# Public endpoints — no key required
_PUBLIC_PATHS = {"/", "/api/health", "/api/docs", "/api/redoc",
                 "/openapi.json", "/api/portfolio/demo"}

async def require_api_key(
    api_key: Optional[str] = Security(_api_key_header),
) -> str:
    """Validate API key. Returns the key tier on success."""
    if _MASTER_KEY and api_key == _MASTER_KEY:
        return "master"
    if api_key == _DEMO_KEY:
        return "demo"
    if not _MASTER_KEY and api_key is None:
        # Dev mode — no key configured, allow all access
        return "dev"
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail={
            "error":   "UNAUTHORIZED",
            "message": "Valid X-ANUBIS-API-KEY header required.",
            "info":    "Contact info.rstanfield@gmail.com for a license key.",
        }
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  SQLITE PERSISTENCE LAYER
# ═══════════════════════════════════════════════════════════════════════════════
_DB_PATH = os.getenv("ANUBIS_DB_PATH", "./anubis.db")

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS compliance_platforms (
            platform_id   TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            platform_type TEXT NOT NULL DEFAULT 'broker',
            description   TEXT DEFAULT '',
            registered_at TEXT NOT NULL,
            last_check    TEXT,
            compliance_score REAL,
            status        TEXT DEFAULT 'pending'
        );
        CREATE TABLE IF NOT EXISTS compliance_alerts (
            alert_id    TEXT PRIMARY KEY,
            rule_id     TEXT,
            rule_name   TEXT,
            metric      TEXT,
            actual      REAL,
            required    TEXT,
            severity    TEXT,
            platform_id TEXT,
            timestamp   TEXT NOT NULL,
            resolved    INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS compliance_rules_custom (
            rule_id   TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            metric    TEXT NOT NULL,
            operator  TEXT NOT NULL,
            threshold REAL NOT NULL,
            severity  TEXT NOT NULL DEFAULT 'WARNING',
            enabled   INTEGER DEFAULT 1,
            built_in  INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analysis_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT NOT NULL,
            portfolio_stage INTEGER,
            portfolio_trap  REAL,
            total_value     REAL,
            holding_count   INTEGER,
            api_key_tier    TEXT
        );
        CREATE TABLE IF NOT EXISTS license_activations (
            activation_id TEXT PRIMARY KEY,
            key_hash      TEXT NOT NULL,
            tier          TEXT NOT NULL,
            activated_at  TEXT NOT NULL,
            last_seen     TEXT NOT NULL,
            request_count INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
#  SAP FRAMEWORK CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SAP_LABELS: Dict[int, str] = {
    0: "Total Loss",        1: "Critical Risk",     2: "Active Decline",
    3: "Stress Zone",       4: "Inflection Point",  5: "Neutral Zone",
    6: "Bullish Trend",     7: "High Alpha",        8: "Overextended",
    9: "Elite Alpha",
}
SAP_COLORS: Dict[int, str] = {
    0: "#dc2626", 1: "#ef4444", 2: "#f97316",
    3: "#fb923c", 4: "#eab308", 5: "#22c55e",
    6: "#16a34a", 7: "#3b82f6", 8: "#a855f7",  9: "#f59e0b",
}
SAP_DESCRIPTIONS: Dict[int, str] = {
    0: "Total loss. Emergency liquidation or portfolio wipeout. Immediate action required.",
    1: "Critical risk. Multiple positions in severe drawdown with no stabilization.",
    2: "Active decline. Sustained losses with no clear recovery signal.",
    3: "Stress zone. High volatility pressure across positions, coherence breaking down.",
    4: "Inflection point. Volatility elevated but recovery capacity is present.",
    5: "Neutral zone. Balanced risk/reward ratio. Holding steady.",
    6: "Bullish trend. Positive price momentum building across positions.",
    7: "High Alpha. Strong trend consistency and high resilience — performing well.",
    8: "Overextended. Surface metrics appear strong — FALSE BREAKOUT risk. Fragility Index elevated.",
    9: "Elite Alpha. Rare, sustained, exceptional multi-position performance.",
}
TRADER_ARCHETYPES: Dict[int, str] = {
    0: "The Paralyzed",        1: "The Panic Seller",      2: "The Distressed Trader",
    3: "The Trigger Trader",   4: "The Student Trader",    5: "The Disciplined Trader",
    6: "The Position Builder", 7: "The Tactical Trader",   8: "The Overleveraged",
    9: "The Alpha Trader",
}

YUNUS_ARROGANCE_MARKERS = [
    "guaranteed win", "can't lose", "sure thing", "100% profit", "no risk",
    "always right", "i know exactly", "can't go wrong", "certain to go up",
    "definitely buying", "fool-proof", "i never lose", "this will moon",
    "zero chance of loss", "i know for certain", "absolutely certain",
    "it's obvious", "no doubt", "trust me on this", "guaranteed upside",
    "risk free", "no way it drops", "easy money", "obvious buy",
]

REROUTE_FRACTION = 0.60       # Adaptive Rebalancer — reroute fraction
REGEN_HEALTH_BOOST = 65.0     # Stop-Loss & Replace — regenerated position initial score
READMIT_THRESHOLD  = 70.0     # Stop-Loss & Replace — readmission threshold

# ═══════════════════════════════════════════════════════════════════════════════
#  REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════
class HoldingInput(BaseModel):
    ticker:   str
    shares:   float = Field(10.0, gt=0)
    avg_cost: float = Field(0.0,  ge=0,  description="0 = use current price")

class UserBehavior(BaseModel):
    win_rate:              float = Field(0.50, ge=0, le=1)
    avg_hold_days:         float = Field(30,   ge=0)
    top3_concentration:    float = Field(0.45, ge=0, le=1)
    max_drawdown:          float = Field(0.15, ge=0, le=1)
    leverage_ratio:        float = Field(1.0,  ge=0)
    plan_override_count:   int   = Field(0,    ge=0)
    portfolio_correlation: float = Field(0.5,  ge=-1, le=1)

class AnalyzeRequest(BaseModel):
    holdings:      List[HoldingInput]
    user_behavior: Optional[UserBehavior] = None

class DisciplineScanRequest(BaseModel):
    text:      str
    stage:     int   = Field(5,   ge=0, le=9)
    coherence: float = Field(5.0, ge=0, le=10)

# Alias for backwards compatibility
YunusScanRequest = DisciplineScanRequest

class AddHoldingRequest(BaseModel):
    ticker:   str
    shares:   float = Field(10.0, gt=0)
    avg_cost: float = Field(0.0,  ge=0)

# ── Compliance / Overwatch Models ─────────────────────────────────────────────
class ComplianceRuleCreate(BaseModel):
    name:        str   = Field(..., description="Rule name, e.g. 'Max Drawdown'")
    metric:      str   = Field(..., description="portfolio_stage | fragility_index | pnl_pct | concentration | leverage | drawdown | stage_8_count | stage_0_1_count")
    operator:    str   = Field(..., description="lt | gt | lte | gte")
    threshold:   float = Field(..., description="Numeric threshold value")
    severity:    str   = Field("WARNING", description="INFO | WARNING | CRITICAL")
    enabled:     bool  = Field(True)

class PlatformRegister(BaseModel):
    name:         str  = Field(..., description="Platform display name, e.g. 'TD Ameritrade Account'")
    platform_type: str = Field("broker", description="broker | prop_firm | fund | personal")
    description:  str  = Field("", description="Optional notes")

class ComplianceCheckRequest(BaseModel):
    platform_id:    Optional[str] = Field(None, description="Platform ID to tag the check to")
    holdings:       List[HoldingInput]
    user_behavior:  Optional[UserBehavior] = None

# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION TRAJECTORY STATE
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class PortfolioSnapshot:
    timestamp:         float
    portfolio_stage:   int
    user_stage:        int
    trap_score:        float
    coherence:         float
    stability:         float

class SessionTrajectory:
    """Position Trajectory Tracker — session-level momentum and recovery metrics."""

    def __init__(self) -> None:
        self.snapshots:            List[PortfolioSnapshot] = []
        self.last_stable:          Optional[PortfolioSnapshot] = None
        self.drawdown_alert_active: bool = False

    @property
    def harrowing_active(self) -> bool:
        """Backwards-compatible alias for drawdown_alert_active."""
        return self.drawdown_alert_active

    def record(self, snap: PortfolioSnapshot) -> None:
        self.snapshots.append(snap)
        # Auto-lock last healthy baseline (Stage 4-6, Fragility Index < 0.5)
        if 4 <= snap.portfolio_stage <= 6 and snap.trap_score < 0.5:
            self.last_stable = snap
        self.drawdown_alert_active = snap.trap_score > 0.80 or snap.portfolio_stage <= 2

    def get_metrics(self) -> Dict:
        n = len(self.snapshots)
        base = {
            "sample_count":       n,
            "harrowing_active":   self.drawdown_alert_active,   # legacy key
            "drawdown_alert":     self.drawdown_alert_active,
            "last_stable_stage":  self.last_stable.portfolio_stage if self.last_stable else None,
            "last_stable_at":     (datetime.fromtimestamp(self.last_stable.timestamp)
                                   .strftime("%Y-%m-%d %H:%M")
                                   if self.last_stable else None),
        }
        if n < 2:
            base.update({"stage_velocity": 0.0, "risk_momentum": 0.0,
                          "rigidity_index": 0.0, "recovery_index": 0.0,
                          "label": "STABLE", "stage_history": [],
                          "trap_history": []})
            return base

        stages = [s.portfolio_stage for s in self.snapshots]
        traps  = [s.trap_score      for s in self.snapshots]

        # Stage velocity dS/dt
        deltas = [stages[i+1] - stages[i] for i in range(n-1)]
        stage_velocity = sum(deltas) / len(deltas)

        # Risk momentum: change in trap trend across halves
        mid = max(n // 2, 1)
        risk_momentum = (sum(traps[mid:]) / max(n - mid, 1)) - (sum(traps[:mid]) / mid)

        # Rigidity index: fraction at Stage 7-8
        rigidity_index = sum(1 for s in stages if s >= 7) / n

        # Recovery index: trap events that resolved
        trap_events = sum(1 for t in traps if t > 0.7)
        resolved    = sum(1 for i, t in enumerate(traps)
                         if t > 0.7 and i+1 < n and traps[i+1] <= 0.7)
        recovery_index = resolved / max(trap_events, 1)

        # Trajectory label
        if stage_velocity >  0.5 and risk_momentum > 0.1:  label = "ESCALATING"
        elif stage_velocity >  0.3:                          label = "ASCENDING"
        elif stage_velocity < -0.3 and risk_momentum < -0.1: label = "RECOVERING"
        elif rigidity_index > 0.6:                           label = "TRAPPED"
        elif abs(stage_velocity) < 0.2:                      label = "STABLE"
        else:                                                 label = "OSCILLATING"

        base.update({
            "stage_velocity":  round(stage_velocity,  3),
            "risk_momentum":   round(risk_momentum,   3),
            "rigidity_index":  round(rigidity_index,  3),
            "recovery_index":  round(recovery_index,  3),
            "label":           label,
            "stage_history":   stages[-30:],
            "trap_history":    [round(t, 3) for t in traps[-30:]],
        })
        return base

# ═══════════════════════════════════════════════════════════════════════════════
#  CORE ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class AnubisEngine:

    def _seed(self, ticker: str) -> float:
        h = int(hashlib.md5(ticker.upper().encode()).hexdigest()[:8], 16)
        return (h % 1000) / 1000.0

    # ── Market data ──────────────────────────────────────────────────────────
    def get_stock_data(self, ticker: str) -> Dict:
        if YFINANCE_AVAILABLE:
            try:
                stk  = yf.Ticker(ticker)
                hist = stk.history(period="1mo")
                info = stk.info or {}
                if not hist.empty and len(hist) >= 2:
                    cur  = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    w5   = float(hist["Close"].iloc[-5]) if len(hist) >= 5 else prev
                    m0   = float(hist["Close"].iloc[0])
                    vol  = float(hist["Close"].pct_change().std()) * math.sqrt(252)
                    return {
                        "price":            round(cur, 2),
                        "change_pct":       round((cur - prev) / prev * 100, 2),
                        "week_change_pct":  round((cur - w5)   / w5   * 100, 2),
                        "month_change_pct": round((cur - m0)   / m0   * 100, 2),
                        "volatility":       round(min(vol, 2.0), 3),
                        "volume":           int(hist["Volume"].iloc[-1]),
                        "pe_ratio":         info.get("trailingPE"),
                        "market_cap":       info.get("marketCap", 0),
                        "real_data":        True,
                    }
            except Exception:
                pass

        # Deterministic mock
        s = self._seed(ticker)
        bases = {"AAPL": 185, "MSFT": 415, "NVDA": 890, "TSLA": 175,
                 "AMZN": 195, "META": 520, "GOOGL": 175, "SPY": 510,
                 "BTC-USD": 68000, "ETH-USD": 3200}
        base  = bases.get(ticker.upper(), 50 + s * 200)
        price = round(base * (0.92 + s * 0.16), 2)
        chg   = round((s - 0.5) * 7, 2)
        vol   = round(0.18 + s * 0.55, 3)
        return {
            "price":            price,
            "change_pct":       chg,
            "week_change_pct":  round(chg * 2.1, 2),
            "month_change_pct": round(chg * 5.8, 2),
            "volatility":       min(vol, 1.5),
            "volume":           int(3_000_000 * s + 500_000),
            "pe_ratio":         None,
            "market_cap":       0,
            "real_data":        False,
        }

    # ── NSDT dimensions ───────────────────────────────────────────────────────
    def _assess_dims(self, ticker: str, data: Dict) -> Dict[str, float]:
        s   = self._seed(ticker)
        pmo = data["month_change_pct"]
        pwk = data["week_change_pct"]
        vol = min(data["volatility"], 1.5)
        chg = data["change_pct"]

        adaptability = max(0, min(10, 5 + pmo / 5 + (s - 0.5) * 2))
        coherence    = max(0, min(10, 10 - vol * 10 + (s - 0.5) * 1.5))
        tension      = max(0, min(10, vol * 14 + max(0, -chg) * 0.4))
        stability    = max(0, min(10, 5 + pwk * 0.35 + pmo * 0.12 + (s - 0.3) * 2))
        return {
            "adaptability": round(adaptability, 2),
            "coherence":    round(coherence, 2),
            "tension":      round(tension, 2),
            "stability":    round(stability, 2),
        }

    # ── Stage + TrapScore ─────────────────────────────────────────────────────
    def _dims_to_stage(self, dims: Dict) -> Tuple[int, float]:
        raw = (dims["adaptability"] * 0.35 + dims["coherence"] * 0.30
               + dims["stability"] * 0.25 - dims["tension"] * 0.10) / 10 * 9
        stage = max(0, min(9, int(raw)))
        trap = 0.0
        if stage >= 7:
            trap = max(0, (dims["coherence"] - dims["adaptability"]) / 10) * 2
            trap += max(0, dims["tension"] - 3) / 15
            trap = min(1.0, trap)
            if trap > 0.6:
                stage = min(stage, 8)
        return stage, round(trap, 3)

    # ── False Breakout detection (formerly False Light) ───────────────────────
    def detect_false_breakout(self, stage: int, dims: Dict, trap_score: float) -> bool:
        """Detects deceptive rally or overextension masking imminent reversal."""
        if stage >= 8 and dims["coherence"] < 3.0:
            return True
        if stage >= 7 and trap_score > 0.72:
            return True
        return False

    # Backwards-compatible alias
    detect_false_light = detect_false_breakout

    # ── Full holding assessment ───────────────────────────────────────────────
    def assess_holding(self, h: HoldingInput) -> Dict:
        data  = self.get_stock_data(h.ticker)
        dims  = self._assess_dims(h.ticker, data)
        stage, trap_comp = self._dims_to_stage(dims)

        # Full TrapScore
        trap_score = trap_comp
        if stage >= 7:
            trap_score += max(0, dims["coherence"] - dims["adaptability"]) / 20
            trap_score += max(0, dims["tension"] - 5) / 20
        trap_score = round(min(1.0, trap_score), 3)

        false_light       = self.detect_false_breakout(stage, dims, trap_score)
        reroute_suggested = stage <= 2
        reroute_pct       = int(REROUTE_FRACTION * 100) if reroute_suggested else 0

        cur   = data["price"]
        cost  = h.avg_cost if h.avg_cost > 0 else round(cur * 0.88, 2)
        value = round(cur * h.shares, 2)
        pnl   = round((cur - cost) / cost * 100, 2)

        if false_light:
            desc = (f"⚠️ FALSE BREAKOUT — Stage {stage} price action appears strong but "
                    "trend consistency is collapsing. Recommend re-evaluation at Stage 5.")
        elif stage <= 2:
            desc = (f"🔴 CRITICAL — {SAP_DESCRIPTIONS[stage]} "
                    f"Adaptive Rebalancer recommends rerouting {reroute_pct}% "
                    "to higher-stage positions.")
        elif stage == 8:
            desc = (f"⚡ OVEREXTENDED — Fragility Index {trap_score:.2f}. "
                    "Surface rally masking overextension. Circuit Breaker risk if trend reverses.")
        else:
            desc = SAP_DESCRIPTIONS[stage]

        return {
            "ticker":            h.ticker.upper(),
            "stage":             stage,
            "stage_label":       SAP_LABELS[stage],
            "stage_color":       SAP_COLORS[stage],
            "price":             cur,
            "change_pct":        data["change_pct"],
            "week_change_pct":   data["week_change_pct"],
            "month_change_pct":  data["month_change_pct"],
            "volatility":        round(data["volatility"] * 100, 1),
            "shares":            h.shares,
            "avg_cost":          cost,
            "position_value":    value,
            "pnl_pct":           pnl,
            "trap_score":        trap_score,
            "false_light":       false_light,
            "reroute_suggested": reroute_suggested,
            "reroute_pct":       reroute_pct,
            "description":       desc,
            "dimensions":        dims,
            "real_data":         data["real_data"],
        }

    # ── Trader behavioral stage (OMEGA PortfolioAnalyzer) ────────────────────
    def assess_user(self, b: UserBehavior) -> Dict:
        adapt = b.win_rate * 10
        coher = max(0, 10 - b.max_drawdown * 40)
        tension = min(10, b.top3_concentration * 8 + max(0, b.leverage_ratio - 1) * 3)
        stab  = min(10, math.log1p(b.avg_hold_days) * 1.8)
        dims  = {"adaptability": round(adapt, 2), "coherence": round(coher, 2),
                 "tension": round(tension, 2), "stability": round(stab, 2)}

        raw   = (adapt * 0.35 + coher * 0.30 + stab * 0.25 - tension * 0.10) / 10 * 9
        stage = max(0, min(9, int(raw)))

        # TrapScore: overconfidence behavioral markers
        trap = 0.0
        trap += min(0.40, b.plan_override_count * 0.08)
        trap += min(0.30, max(0, b.leverage_ratio - 1.0) * 0.22)
        if b.top3_concentration > 0.70:
            trap += 0.18
        trap_score = round(min(1.0, trap), 3)

        yunus_score = round(max(0, min(100,
            100 - trap_score * 60
                - b.plan_override_count * 5
                - max(0, b.leverage_ratio - 1) * 14
                - max(0, b.top3_concentration - 0.60) * 28
        )), 1)

        archetype  = TRADER_ARCHETYPES.get(stage, "Unknown")
        trap_risk  = trap_score > 0.50 or stage == 8

        if false_light_risk := (stage >= 8 and coher < 3.0):
            desc = (f"⚠️ FALSE BREAKOUT — Trader at Stage {stage} displaying overextension "
                    "patterns. Fragility Index elevated. Controlled Exposure Reduction recommended.")
        elif trap_risk:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    f"Fragility Index {trap_score:.2f}. Overextension trap risk. Review position sizing and leverage.")
        elif stage >= 6:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    "Disciplined execution with solid risk management ratios.")
        else:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    "Key behavioral metrics indicate room for trading discipline improvement.")

        return {
            "user_stage":    stage,
            "stage_label":   SAP_LABELS[stage],
            "stage_color":   SAP_COLORS[stage],
            "archetype":     archetype,
            "trap_risk":     trap_risk,
            "false_light":   false_light_risk,
            "trap_score":    trap_score,
            "yunus_score":   yunus_score,
            "description":   desc,
            "dimensions":    dims,
        }

    # ── Discipline Protocol (Hubris Scanner) ─────────────────────────────────
    def yunus_scan(self, text: str, stage: int = 5, coherence: float = 5.0) -> Dict:
        """Discipline Protocol: HUBRIS_SCANNER + FALSE_BREAKOUT_DETECTION + CONTROLLED_EXPOSURE_REDUCTION."""
        tl = text.lower()
        detected = [m for m in YUNUS_ARROGANCE_MARKERS if m in tl]

        score = max(0, 100 - len(detected) * 14)
        flags = []
        if len(detected) >= 2:
            flags.append("OVEREXTENSION_TRAP")
        if any(m in tl for m in ["no risk", "can't lose", "100% profit", "risk free"]):
            flags.append("MISSING_DOWNSIDE_SCENARIO")

        # False Breakout check (formerly False Light)
        false_breakout = stage >= 8 and coherence < 3.0
        if false_breakout:
            flags.append("FALSE_BREAKOUT_DETECTED")
            score = min(score, 35)

        output_safe = score >= 70 and not false_breakout

        if false_breakout:
            rec = ("FALSE BREAKOUT DETECTED: Re-evaluate position at Stage 5. "
                   "Surface price strength is not supported by underlying trend consistency.")
        elif "OVEREXTENSION_TRAP" in flags:
            rec = (f"CONTROLLED EXPOSURE REDUCTION: Reduce position sizes 30-40%. "
                   f"Overconfidence markers detected: {', '.join(detected[:3])}. "
                   "Downside scenario has not been accounted for.")
        elif detected:
            rec = (f"Hubris signals detected: {', '.join(detected[:2])}. "
                   "Re-examine risk assumptions before executing.")
        else:
            rec = "Trading discipline maintained. Notes appear risk-aware and grounded."

        return {
            "output_safe":       output_safe,
            "yunus_score":       round(score, 1),    # key kept for API compatibility
            "discipline_score":  round(score, 1),    # preferred new key
            "detected_markers":  detected,
            "flags":             flags,
            "false_light":       false_breakout,     # legacy key
            "false_breakout":    false_breakout,
            "recommendation":    rec,
        }

    # ── InfraAdaptiveCamouflage: rebalance suggestions ────────────────────────
    def get_rebalance_suggestions(self, analyzed: List[Dict]) -> List[Dict]:
        critical = [h for h in analyzed if h["stage"] <= 2]
        healthy  = [h for h in analyzed if h["stage"] >= 5]
        if not critical or not healthy:
            return []
        sugg = []
        total_healthy_val = sum(h["position_value"] for h in healthy) or 1
        for c in critical[:3]:
            for h in healthy:
                weight = h["position_value"] / total_healthy_val
                pct    = round(REROUTE_FRACTION * weight * 100, 1)
                if pct >= 1.0:
                    sugg.append({
                        "from_ticker": c["ticker"],
                        "to_ticker":   h["ticker"],
                        "pct":         pct,
                        "from_stage":  c["stage"],
                        "to_stage":    h["stage"],
                        "rationale":   (f"Move {pct}% of {c['ticker']} "
                                        f"(Stage {c['stage']}) → {h['ticker']} "
                                        f"(Stage {h['stage']})"),
                    })
        return sorted(sugg, key=lambda x: -x["pct"])[:6]

    # ── CITI: Systemic Tumbling Alert ─────────────────────────────────────────
    def systemic_alert(self, portfolio_stage: int, user_stage: int,
                       portfolio_trap: float) -> Dict:
        domains = []
        if portfolio_stage <= 3:
            domains.append("portfolio")
        if user_stage <= 3:
            domains.append("trader_behavior")
        if portfolio_trap > 0.75:
            domains.append("trap_risk")

        level  = len(domains)
        labels = {0: "CLEAR", 1: "CAUTION", 2: "WARNING", 3: "SYSTEMIC_ALERT"}
        colors = {0: "#22c55e", 1: "#eab308", 2: "#f97316", 3: "#dc2626"}
        return {
            "active":             level >= 1,
            "level":              level,
            "label":              labels.get(level, "SYSTEMIC_ALERT"),
            "color":              colors.get(level, "#dc2626"),
            "domains_declining":  domains,
            "description": (
                "SYSTEMIC COLLAPSE RISK — Multiple domains deteriorating simultaneously."
                if level >= 3 else
                "Multi-domain stress — portfolio and behavioral risk converging."
                if level == 2 else
                "Single domain under stress. Monitor for deterioration spread."
                if level == 1 else
                "All monitored domains stable."
            ),
        }

# ═══════════════════════════════════════════════════════════════════════════════
#  COMPLIANCE / OVERWATCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
import uuid as _uuid

_METRIC_DISPLAY = {
    "portfolio_stage":  "Portfolio Stage",
    "fragility_index":  "Fragility Index",
    "pnl_pct":          "Portfolio P&L %",
    "concentration":    "Top-3 Concentration",
    "leverage":         "Leverage Ratio",
    "drawdown":         "Max Drawdown %",
    "stage_8_count":    "Stage-8 (Overextended) Count",
    "stage_0_1_count":  "Stage-0/1 (Critical) Count",
}

class ComplianceEngine:
    """
    ANUBIS Compliance & Overwatch Layer — monitors registered trading platforms
    against user-defined risk rules and generates a timestamped violation log.
    """

    def __init__(self) -> None:
        # In-memory cache (populated from DB on startup)
        self._builtin_rules: List[Dict] = []
        self._seed_default_rules()
        self._load_from_db()

    def _load_from_db(self) -> None:
        """Load persisted platforms, custom rules, and recent alerts from SQLite."""
        try:
            conn = _get_db()
            # Custom rules
            rows = conn.execute("SELECT * FROM compliance_rules_custom ORDER BY rowid").fetchall()
            self._custom_rules: List[Dict] = [dict(r) for r in rows]
            for r in self._custom_rules:
                r["enabled"]  = bool(r["enabled"])
                r["built_in"] = bool(r["built_in"])
            # Platforms
            self._platforms: List[Dict] = [dict(r) for r in
                conn.execute("SELECT * FROM compliance_platforms ORDER BY registered_at").fetchall()]
            # Recent alerts (last 200)
            self._alerts: List[Dict] = [dict(r) for r in
                conn.execute("SELECT * FROM compliance_alerts ORDER BY timestamp DESC LIMIT 200").fetchall()]
            for a in self._alerts:
                a["resolved"] = bool(a["resolved"])
            conn.close()
        except Exception:
            self._custom_rules = []
            self._platforms    = []
            self._alerts       = []

    @property
    def rules(self) -> List[Dict]:
        return self._builtin_rules + self._custom_rules

    @property
    def platforms(self) -> List[Dict]:
        return self._platforms

    @property
    def alerts(self) -> List[Dict]:
        return self._alerts

    # ── Default built-in rules ────────────────────────────────────────────────
    def _seed_default_rules(self) -> None:
        defaults = [
            {"name": "Min Portfolio Stage",      "metric": "portfolio_stage",  "operator": "gte", "threshold": 3.0,  "severity": "WARNING",  "enabled": True},
            {"name": "Max Fragility Index",       "metric": "fragility_index",  "operator": "lte", "threshold": 0.75, "severity": "WARNING",  "enabled": True},
            {"name": "Max Critical Holdings",     "metric": "stage_0_1_count",  "operator": "lte", "threshold": 1.0,  "severity": "CRITICAL", "enabled": True},
            {"name": "Max Overextended Count",    "metric": "stage_8_count",    "operator": "lte", "threshold": 2.0,  "severity": "WARNING",  "enabled": True},
            {"name": "Max Portfolio Drawdown",    "metric": "drawdown",         "operator": "gte", "threshold": -25.0,"severity": "CRITICAL", "enabled": True},
            {"name": "Max Concentration (Top-3)", "metric": "concentration",    "operator": "lte", "threshold": 0.60, "severity": "WARNING",  "enabled": True},
        ]
        for d in defaults:
            d["rule_id"] = str(_uuid.uuid4())[:8]
            d["built_in"] = True
            self._builtin_rules.append(d)

    # ── Rule CRUD ─────────────────────────────────────────────────────────────
    def add_rule(self, r: ComplianceRuleCreate) -> Dict:
        rule = r.dict()
        rule["rule_id"]    = str(_uuid.uuid4())[:8]
        rule["built_in"]   = False
        rule["created_at"] = datetime.utcnow().isoformat() + "Z"
        try:
            conn = _get_db()
            conn.execute(
                "INSERT INTO compliance_rules_custom VALUES (:rule_id,:name,:metric,:operator,:threshold,:severity,:enabled,:built_in,:created_at)",
                {**rule, "enabled": 1 if rule.get("enabled") else 0, "built_in": 0}
            )
            conn.commit(); conn.close()
        except Exception: pass
        self._custom_rules.append(rule)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        # Only custom rules can be deleted
        before = len(self._custom_rules)
        self._custom_rules = [r for r in self._custom_rules if r["rule_id"] != rule_id]
        if len(self._custom_rules) < before:
            try:
                conn = _get_db()
                conn.execute("DELETE FROM compliance_rules_custom WHERE rule_id=?", (rule_id,))
                conn.commit(); conn.close()
            except Exception: pass
            return True
        # Toggle built-in rule disabled instead of delete
        for r in self._builtin_rules:
            if r["rule_id"] == rule_id:
                r["enabled"] = False
                return True
        return False

    def toggle_rule(self, rule_id: str) -> Optional[Dict]:
        for r in self._builtin_rules + self._custom_rules:
            if r["rule_id"] == rule_id:
                r["enabled"] = not r["enabled"]
                if not r.get("built_in"):
                    try:
                        conn = _get_db()
                        conn.execute("UPDATE compliance_rules_custom SET enabled=? WHERE rule_id=?",
                                     (1 if r["enabled"] else 0, rule_id))
                        conn.commit(); conn.close()
                    except Exception: pass
                return r
        return None

    # ── Platform registry ─────────────────────────────────────────────────────
    def register_platform(self, p: PlatformRegister) -> Dict:
        plat = p.dict()
        plat["platform_id"]      = str(_uuid.uuid4())[:8]
        plat["registered_at"]    = datetime.utcnow().isoformat() + "Z"
        plat["last_check"]       = None
        plat["compliance_score"] = None
        plat["status"]           = "pending"
        try:
            conn = _get_db()
            conn.execute(
                "INSERT INTO compliance_platforms VALUES (:platform_id,:name,:platform_type,:description,:registered_at,:last_check,:compliance_score,:status)",
                plat
            )
            conn.commit(); conn.close()
        except Exception: pass
        self._platforms.append(plat)
        return plat

    def delete_platform(self, platform_id: str) -> bool:
        before = len(self._platforms)
        self._platforms = [p for p in self._platforms if p["platform_id"] != platform_id]
        if len(self._platforms) < before:
            try:
                conn = _get_db()
                conn.execute("DELETE FROM compliance_platforms WHERE platform_id=?", (platform_id,))
                conn.commit(); conn.close()
            except Exception: pass
            return True
        return False

    # ── Core compliance check ─────────────────────────────────────────────────
    def _extract_metrics(self, holdings: List[Dict], pnl_pct: float,
                         user: Optional[Dict] = None) -> Dict:
        total_val         = sum(h["position_value"] for h in holdings) or 1
        stage_0_1_count   = sum(1 for h in holdings if h["stage"] <= 1)
        stage_8_count     = sum(1 for h in holdings if h["stage"] == 8)
        top3_val          = sum(h["position_value"] for h in
                               sorted(holdings, key=lambda x: -x["position_value"])[:3])
        concentration     = round(top3_val / total_val, 4)
        max_fragility     = max((h["trap_score"] for h in holdings), default=0.0)
        portfolio_stage   = max(0, min(9, round(
            sum(h["stage"] * h["position_value"] for h in holdings) / total_val
        )))
        # Worst individual pnl as drawdown proxy
        drawdown_pct      = min((h["pnl_pct"] for h in holdings), default=0.0)

        return {
            "portfolio_stage": portfolio_stage,
            "fragility_index": max_fragility,
            "pnl_pct":         pnl_pct,
            "concentration":   concentration,
            "leverage":        user["dimensions"].get("tension", 5.0) / 5.0 if user else 1.0,
            "drawdown":        drawdown_pct,
            "stage_8_count":   stage_8_count,
            "stage_0_1_count": stage_0_1_count,
        }

    def _eval_rule(self, rule: Dict, metrics: Dict) -> Optional[Dict]:
        """Returns a violation dict if rule is triggered, else None."""
        if not rule.get("enabled", True):
            return None
        metric    = rule["metric"]
        operator  = rule["operator"]
        threshold = rule["threshold"]
        value     = metrics.get(metric)
        if value is None:
            return None
        ops = {"lt": lambda a, b: a < b,  "gt":  lambda a, b: a > b,
               "lte": lambda a, b: a <= b, "gte": lambda a, b: a >= b}
        op_fn = ops.get(operator)
        if not op_fn:
            return None
        # Rule PASSES when condition is met; VIOLATION when condition is NOT met
        # e.g. "portfolio_stage gte 3" = portfolio_stage must be >= 3
        if not op_fn(value, threshold):
            op_display = {"lt": "<", "gt": ">", "lte": "≤", "gte": "≥"}.get(operator, operator)
            return {
                "rule_id":   rule["rule_id"],
                "rule_name": rule["name"],
                "metric":    _METRIC_DISPLAY.get(metric, metric),
                "actual":    round(value, 3),
                "required":  f"{op_display} {threshold}",
                "severity":  rule["severity"],
            }
        return None

    def run_check(self, holdings: List[Dict], pnl_pct: float,
                  user: Optional[Dict], platform_id: Optional[str] = None) -> Dict:
        metrics    = self._extract_metrics(holdings, pnl_pct, user)
        violations = []
        for rule in self.rules:
            v = self._eval_rule(rule, metrics)
            if v:
                violations.append(v)

        critical_count = sum(1 for v in violations if v["severity"] == "CRITICAL")
        warning_count  = sum(1 for v in violations if v["severity"] == "WARNING")
        total_rules    = sum(1 for r in self.rules if r.get("enabled", True))
        passed         = total_rules - len(violations)
        score          = round(max(0, 100 - critical_count * 25 - warning_count * 10), 1)

        status = ("FAIL"    if critical_count > 0 else
                  "CAUTION" if warning_count  > 0 else
                  "PASS")
        color  = {"PASS": "#22c55e", "CAUTION": "#eab308", "FAIL": "#dc2626"}.get(status)

        result = {
            "platform_id":     platform_id,
            "timestamp":       datetime.utcnow().isoformat() + "Z",
            "compliance_score": score,
            "status":          status,
            "status_color":    color,
            "rules_checked":   total_rules,
            "rules_passed":    passed,
            "violations":      violations,
            "critical_count":  critical_count,
            "warning_count":   warning_count,
            "metrics_snapshot": metrics,
        }

        # Record to alert log (in-memory + DB)
        if violations:
            try:
                conn = _get_db()
                for v in violations:
                    alert = {**v,
                        "alert_id":    str(_uuid.uuid4())[:8],
                        "platform_id": platform_id,
                        "timestamp":   result["timestamp"],
                        "resolved":    False,
                    }
                    self._alerts.insert(0, alert)
                    conn.execute(
                        "INSERT OR REPLACE INTO compliance_alerts VALUES "
                        "(:alert_id,:rule_id,:rule_name,:metric,:actual,:required,:severity,:platform_id,:timestamp,0)",
                        {**alert, "rule_id": alert.get("rule_id",""), "resolved": 0}
                    )
                conn.commit(); conn.close()
            except Exception as _e:
                pass
            # Keep last 200 in memory
            self._alerts = self._alerts[:200]

        # Update platform record (in-memory + DB)
        for p in self._platforms:
            if p["platform_id"] == platform_id:
                p["last_check"]       = result["timestamp"]
                p["compliance_score"] = score
                p["status"]           = status
                try:
                    conn = _get_db()
                    conn.execute(
                        "UPDATE compliance_platforms SET last_check=?,compliance_score=?,status=? WHERE platform_id=?",
                        (result["timestamp"], score, status, platform_id)
                    )
                    conn.commit(); conn.close()
                except Exception: pass
                break

        return result

    def clear_alerts(self) -> int:
        n = len(self._alerts)
        self._alerts = []
        try:
            conn = _get_db()
            conn.execute("DELETE FROM compliance_alerts")
            conn.commit(); conn.close()
        except Exception: pass
        return n

    def resolve_alert(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a["alert_id"] == alert_id:
                a["resolved"] = True
                try:
                    conn = _get_db()
                    conn.execute("UPDATE compliance_alerts SET resolved=1 WHERE alert_id=?", (alert_id,))
                    conn.commit(); conn.close()
                except Exception: pass
                return True
        return False

# ═══════════════════════════════════════════════════════════════════════════════
#  DEFAULT DEMO PORTFOLIO
# ═══════════════════════════════════════════════════════════════════════════════
DEMO_PORTFOLIO = [
    {"ticker": "AAPL",  "shares": 25,  "avg_cost": 155.00},
    {"ticker": "NVDA",  "shares": 10,  "avg_cost": 620.00},
    {"ticker": "TSLA",  "shares": 15,  "avg_cost": 225.00},
    {"ticker": "MSFT",  "shares": 20,  "avg_cost": 350.00},
    {"ticker": "AMZN",  "shares": 8,   "avg_cost": 145.00},
    {"ticker": "META",  "shares": 5,   "avg_cost": 380.00},
]

# ═══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════
app = FastAPI(
    title="ANUBIS — LUMINARK Portfolio Intelligence & Compliance",
    description=(
        "SAP 10-stage portfolio classification, trajectory tracking, "
        "Discipline Protocol, Drawdown Recovery, and Compliance/Overwatch monitoring layer — powered by LUMINARK."
    ),
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_init_db()   # Ensure SQLite tables exist at startup
engine     = AnubisEngine()
session    = SessionTrajectory()
compliance = ComplianceEngine()

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status":    "operational",
        "version":   "3.0.0",
        "product":   "ANUBIS — LUMINARK Portfolio Intelligence & Compliance",
        "copyright": "© 2024-2026 Richard L. Stanfield / MAAT. All Rights Reserved.",
        "patent":    "Pending — USPTO (Application filed March 2026)",
        "yfinance":  YFINANCE_AVAILABLE,
        "real_data": YFINANCE_AVAILABLE,
        "snapshots": len(session.snapshots),
        "compliance_rules":     len(compliance.rules),
        "compliance_platforms": len(compliance.platforms),
        "compliance_alerts":    len(compliance.alerts),
        "auth_mode": "master" if _MASTER_KEY else "dev",
        "demo_key":  _DEMO_KEY if not _MASTER_KEY else None,
    }

@app.get("/api/license",
         summary="License and product information",
         tags=["System"])
async def license_info(key_tier: str = Depends(require_api_key)):
    """Returns product licensing information and API key tier."""
    return {
        "product":        "ANUBIS — LUMINARK Portfolio Intelligence & Compliance Platform",
        "version":        "3.0.0",
        "owner":          "Richard L. Stanfield",
        "organization":   "Meridian Axiom Alignment Technologies (MAAT)",
        "copyright":      "© 2024-2026 Richard L. Stanfield / MAAT. All Rights Reserved.",
        "patent_status":  "Patent Pending — USPTO (Application filed March 2026)",
        "ip_framework":   ["SAP (Stanfield's Asset Progression)", "NSDT Multi-Dimensional Analysis",
                           "LUMINARK Overwatch", "LUMINARK Omega"],
        "key_tier":       key_tier,
        "licensing":      "Commercial licenses available. Contact: info.rstanfield@gmail.com",
        "terms":          "Use of this software is governed by the ANUBIS Commercial License Agreement.",
        "trademark":      "ANUBIS, LUMINARK, SAP, NSDT, MAAT are trademarks of Richard L. Stanfield.",
    }

@app.get("/api/portfolio/demo")
async def demo_portfolio():
    return {"holdings": DEMO_PORTFOLIO, "message": "Demo portfolio loaded — 6 holdings"}

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key)):
    if not req.holdings:
        raise HTTPException(400, "Provide at least one holding.")

    # Per-holding analysis
    analyzed = [engine.assess_holding(h) for h in req.holdings]

    # Portfolio aggregate
    total_val      = sum(h["position_value"] for h in analyzed) or 1
    total_cost     = sum(h["avg_cost"] * h["shares"] for h in analyzed)
    portfolio_pnl  = round((total_val - total_cost) / total_cost * 100, 2)
    w_stage        = sum(h["stage"] * h["position_value"] for h in analyzed) / total_val
    portfolio_stage = max(0, min(9, round(w_stage)))
    portfolio_trap  = max(h["trap_score"] for h in analyzed)
    avg_coherence   = sum(h["dimensions"]["coherence"]  for h in analyzed) / len(analyzed)
    avg_stability   = sum(h["dimensions"]["stability"]  for h in analyzed) / len(analyzed)

    # User behavioral assessment
    ub   = req.user_behavior or UserBehavior()
    user = engine.assess_user(ub)

    # Record to trajectory
    snap = PortfolioSnapshot(
        timestamp=time.time(), portfolio_stage=portfolio_stage,
        user_stage=user["user_stage"], trap_score=portfolio_trap,
        coherence=avg_coherence, stability=avg_stability,
    )
    session.record(snap)
    trajectory = session.get_metrics()

    # Drawdown Recovery Protocol (formerly Harrowing Protocol)
    harrowing = {
        "active":             session.drawdown_alert_active,
        "drawdown_alert":     session.drawdown_alert_active,
        "last_stable_stage":  (session.last_stable.portfolio_stage
                               if session.last_stable else None),
        "last_stable_at":     (datetime.fromtimestamp(session.last_stable.timestamp)
                               .strftime("%Y-%m-%d %H:%M")
                               if session.last_stable else None),
        "restoration_action": (
            f"BASELINE RECOVERY SEQUENCE: Target Stage "
            f"{session.last_stable.portfolio_stage} — reduce high-Fragility-Index positions "
            "and reallocate toward Neutral Zone (Stage 5-6) holdings."
            if session.last_stable else
            "No healthy baseline locked yet. Run multiple analyses to establish one."
        ),
        "quarantine_risk":    portfolio_trap > 0.90 or portfolio_stage <= 1,
        "mode": (
            "CIRCUIT_BREAKER"   if portfolio_trap > 0.90 or portfolio_stage <= 1 else
            "DRAWDOWN_ALERT"    if session.drawdown_alert_active else
            "NORMAL"
        ),
    }

    # Threats
    threats = []
    for h in analyzed:
        if h["false_light"]:
            threats.append({"ticker": h["ticker"], "severity": "HIGH",
                            "type": "FALSE_BREAKOUT",
                            "description": f"FALSE BREAKOUT: Stage {h['stage']} — trend consistency collapsing beneath surface rally"})
        elif h["stage"] <= 2:
            threats.append({"ticker": h["ticker"], "severity": "CRITICAL",
                            "type": "CRITICAL_DECLINE",
                            "description": f"Stage {h['stage']} — active decline, stop-loss review required"})
        elif h["trap_score"] > 0.65:
            threats.append({"ticker": h["ticker"], "severity": "MEDIUM",
                            "type": "OVEREXTENSION_RISK",
                            "description": f"Fragility Index {h['trap_score']:.2f} — overextension risk, position sizing review advised"})

    threats.sort(key=lambda t: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(t["severity"], 3))

    rebalance = engine.get_rebalance_suggestions(analyzed)
    systemic  = engine.systemic_alert(portfolio_stage, user["user_stage"], portfolio_trap)

    return {
        "overall_stage":       portfolio_stage,
        "overall_label":       SAP_LABELS[portfolio_stage],
        "overall_color":       SAP_COLORS[portfolio_stage],
        "overall_description": SAP_DESCRIPTIONS[portfolio_stage],
        "overall_trap_score":  round(portfolio_trap, 3),
        "total_value":         round(total_val, 2),
        "total_cost":          round(total_cost, 2),
        "portfolio_pnl_pct":   portfolio_pnl,
        "holdings":            analyzed,
        "user":                user,
        "trajectory":          trajectory,
        "harrowing":           harrowing,
        "threats":             threats,
        "rebalance":           rebalance,
        "systemic_alert":      systemic,
        "real_data":           YFINANCE_AVAILABLE,
        "timestamp":           datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/trajectory")
async def get_trajectory():
    return session.get_metrics()

@app.post("/api/yunus_scan")
async def yunus_scan(req: YunusScanRequest, key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key)):
    return engine.yunus_scan(req.text, req.stage, req.coherence)

@app.get("/api/harrowing_status")
async def harrowing_status():
    """Drawdown Recovery Protocol status — last healthy baseline and recovery mode."""
    return {
        "active":             session.drawdown_alert_active,
        "drawdown_alert":     session.drawdown_alert_active,
        "mode":               ("CIRCUIT_BREAKER"  if
                               session.snapshots and session.snapshots[-1].trap_score > 0.90
                               else "DRAWDOWN_ALERT" if session.drawdown_alert_active else "NORMAL"),
        "last_stable_stage":  (session.last_stable.portfolio_stage
                               if session.last_stable else None),
        "last_stable_at":     (datetime.fromtimestamp(session.last_stable.timestamp)
                               .strftime("%Y-%m-%d %H:%M")
                               if session.last_stable else None),
        "snapshots_recorded":  len(session.snapshots),
        "circuit_breaker_risk": (session.snapshots[-1].trap_score > 0.90
                                 if session.snapshots else False),
    }

# ── Compliance / Overwatch Routes ─────────────────────────────────────────────

@app.get("/api/compliance/rules",
         summary="List all compliance rules",
         tags=["Compliance"])
async def list_compliance_rules():
    """Returns all active compliance rules including built-in defaults."""
    return {"rules": compliance.rules, "count": len(compliance.rules)}

@app.post("/api/compliance/rules",
          summary="Add a compliance rule",
          tags=["Compliance"])
async def add_compliance_rule(rule: ComplianceRuleCreate):
    """Create a custom compliance rule. Metric options: portfolio_stage, fragility_index,
    pnl_pct, concentration, leverage, drawdown, stage_8_count, stage_0_1_count."""
    new_rule = compliance.add_rule(rule)
    return {"rule": new_rule, "message": f"Rule '{new_rule['name']}' added (ID: {new_rule['rule_id']})"}

@app.delete("/api/compliance/rules/{rule_id}",
            summary="Delete a compliance rule",
            tags=["Compliance"])
async def delete_compliance_rule(rule_id: str):
    ok = compliance.delete_rule(rule_id)
    if not ok:
        raise HTTPException(404, f"Rule {rule_id} not found")
    return {"deleted": rule_id}

@app.post("/api/compliance/rules/{rule_id}/toggle",
          summary="Enable/disable a compliance rule",
          tags=["Compliance"])
async def toggle_compliance_rule(rule_id: str):
    rule = compliance.toggle_rule(rule_id)
    if not rule:
        raise HTTPException(404, f"Rule {rule_id} not found")
    return {"rule": rule, "message": f"Rule {'enabled' if rule['enabled'] else 'disabled'}"}

@app.get("/api/compliance/platforms",
         summary="List registered monitoring platforms",
         tags=["Compliance"])
async def list_platforms():
    """Returns all registered trading platforms being monitored."""
    return {"platforms": compliance.platforms, "count": len(compliance.platforms)}

@app.post("/api/compliance/platforms",
          summary="Register a trading platform for monitoring",
          tags=["Compliance"])
async def register_platform(p: PlatformRegister):
    """Register a trading platform (broker, prop firm, personal account, etc.) for compliance monitoring."""
    plat = compliance.register_platform(p)
    return {"platform": plat, "message": f"Platform '{plat['name']}' registered (ID: {plat['platform_id']})"}

@app.delete("/api/compliance/platforms/{platform_id}",
            summary="Remove a monitored platform",
            tags=["Compliance"])
async def delete_platform(platform_id: str):
    ok = compliance.delete_platform(platform_id)
    if not ok:
        raise HTTPException(404, f"Platform {platform_id} not found")
    return {"deleted": platform_id}

@app.post("/api/compliance/check",
          summary="Run a compliance check on a portfolio",
          tags=["Compliance"])
async def run_compliance_check(req: ComplianceCheckRequest, key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key), key_tier: str = Depends(require_api_key)):
    """Submit a portfolio for compliance analysis against all enabled rules.
    Optionally tag to a registered platform_id. Returns violations, score, and status."""
    if not req.holdings:
        raise HTTPException(400, "Provide at least one holding.")
    analyzed    = [engine.assess_holding(h) for h in req.holdings]
    total_val   = sum(h["position_value"] for h in analyzed) or 1
    total_cost  = sum(h["avg_cost"] * h["shares"] for h in analyzed)
    pnl_pct     = round((total_val - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0
    ub   = req.user_behavior or UserBehavior()
    user = engine.assess_user(ub)
    return compliance.run_check(analyzed, pnl_pct, user, req.platform_id)

@app.get("/api/compliance/alerts",
         summary="Get compliance violation alert log",
         tags=["Compliance"])
async def get_compliance_alerts(limit: int = 50, unresolved_only: bool = False):
    """Returns the recent compliance violation alert log, newest first."""
    alerts = compliance.alerts
    if unresolved_only:
        alerts = [a for a in alerts if not a.get("resolved")]
    return {
        "alerts":   alerts[:limit],
        "total":    len(compliance.alerts),
        "unresolved": sum(1 for a in compliance.alerts if not a.get("resolved")),
    }

@app.delete("/api/compliance/alerts",
            summary="Clear all compliance alerts",
            tags=["Compliance"])
async def clear_compliance_alerts():
    n = compliance.clear_alerts()
    return {"message": f"Cleared {n} alerts"}

@app.post("/api/compliance/alerts/{alert_id}/resolve",
          summary="Mark an alert as resolved",
          tags=["Compliance"])
async def resolve_alert(alert_id: str):
    ok = compliance.resolve_alert(alert_id)
    if not ok:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return {"resolved": alert_id}

@app.get("/api/compliance/summary",
         summary="Compliance dashboard summary",
         tags=["Compliance"])
async def compliance_summary():
    """High-level compliance status across all platforms."""
    total_platforms  = len(compliance.platforms)
    passing          = sum(1 for p in compliance.platforms if p.get("status") == "PASS")
    failing          = sum(1 for p in compliance.platforms if p.get("status") == "FAIL")
    caution          = sum(1 for p in compliance.platforms if p.get("status") == "CAUTION")
    unresolved_alerts = sum(1 for a in compliance.alerts if not a.get("resolved"))
    avg_score        = (sum(p["compliance_score"] for p in compliance.platforms
                           if p.get("compliance_score") is not None) / max(total_platforms, 1)
                       if total_platforms > 0 else None)
    return {
        "total_platforms":   total_platforms,
        "platforms_passing": passing,
        "platforms_failing": failing,
        "platforms_caution": caution,
        "active_rules":      sum(1 for r in compliance.rules if r.get("enabled")),
        "total_rules":       len(compliance.rules),
        "unresolved_alerts": unresolved_alerts,
        "avg_compliance_score": round(avg_score, 1) if avg_score is not None else None,
        "overall_status": ("FAIL"    if failing > 0 else
                           "CAUTION" if caution > 0 or unresolved_alerts > 0 else
                           "PASS"    if total_platforms > 0 else "NO_PLATFORMS"),
    }

# ── Serve frontend ─────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_static = os.path.join(_here, "static")

@app.get("/", include_in_schema=False)
async def root():
    fp = os.path.join(_static, "index.html")
    if os.path.isfile(fp):
        return FileResponse(fp)
    return JSONResponse({"message": "ANUBIS API is running. See /api/docs"})

if os.path.isdir(_static):
    app.mount("/static", StaticFiles(directory=_static), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
