"""
ANUBIS — LUMINARK-Powered Stock Portfolio Intelligence Platform
FastAPI Backend  |  Version 2.0.0  |  Production Ready
Author: Richard L. Stanfield  |  Meridian Axiom Alignment Technologies

Capabilities:
  • SAP 10-stage portfolio and holding classification (NSDT framework)
  • Real-time stock data via yfinance (falls back to deterministic mock)
  • LuminarkTrajectoryState: session-level stage_velocity, risk_momentum,
    rigidity_index, recovery_index across the full session
  • Yunus Protocol: ARROGANCE_SCANNER + FALSE_LIGHT_DETECTION + COMPASSIONATE_CONTAINMENT
  • Harrowing Protocol: LAST_STABLE_SNAPSHOT + SHADOW_RETRIEVAL + QUARANTINE_MODE
  • InfraAdaptiveCamouflage: 60% reroute from Stage 0-2 holdings to healthy ones
  • InfraIsolateAndRegenerate: quarantine + regeneration suggestions
  • CITI: Systemic Tumbling Alert across portfolio + behavioral domains
  • PortfolioAnalyzer: 7-metric trader behavioral stage assessment
  • Serves the React frontend from /static/index.html
"""

from __future__ import annotations
import math, time, re, os, hashlib, json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ── Optional real-data dependency ─────────────────────────────────────────────
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
#  SAP FRAMEWORK CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SAP_LABELS: Dict[int, str] = {
    0: "System Collapse",   1: "Critical Failure",  2: "Crisis",
    3: "Struggle",          4: "Transition",         5: "Equilibrium",
    6: "Growth",            7: "Peak Performance",   8: "Brittle Peak",
    9: "Transcendence",
}
SAP_COLORS: Dict[int, str] = {
    0: "#dc2626", 1: "#ef4444", 2: "#f97316",
    3: "#fb923c", 4: "#eab308", 5: "#22c55e",
    6: "#16a34a", 7: "#3b82f6", 8: "#a855f7",  9: "#f59e0b",
}
SAP_DESCRIPTIONS: Dict[int, str] = {
    0: "Complete collapse. Emergency action required immediately.",
    1: "Critical failure. Multiple positions at severe risk.",
    2: "Crisis state. Severe drawdown with no clear recovery path.",
    3: "Struggling to stabilize. High stress across positions.",
    4: "In transition. Volatility high but adaptive capacity present.",
    5: "Equilibrium. Balanced risk/reward, holding steady.",
    6: "Growth phase. Positive momentum building across positions.",
    7: "Peak performance. Strong coherence and high adaptability.",
    8: "Brittle Peak. Appears strong — FALSE LIGHT risk. TrapScore elevated.",
    9: "Transcendent performance. Rare, sustained, exceptional.",
}
TRADER_ARCHETYPES: Dict[int, str] = {
    0: "The Frozen",       1: "The Panicked",      2: "The Distressed",
    3: "The Reactive",     4: "The Seeker",         5: "The Balanced",
    6: "The Builder",      7: "The Master",         8: "The Overconfident",
    9: "The Legend",
}

YUNUS_ARROGANCE_MARKERS = [
    "guaranteed win", "can't lose", "sure thing", "100% profit", "no risk",
    "always right", "i know exactly", "can't go wrong", "certain to go up",
    "definitely buying", "fool-proof", "i never lose", "this will moon",
    "zero chance of loss", "i know for certain", "absolutely certain",
    "it's obvious", "no doubt", "trust me on this", "guaranteed upside",
    "risk free", "no way it drops", "easy money", "obvious buy",
]

REROUTE_FRACTION = 0.60       # InfraAdaptiveCamouflage
REGEN_HEALTH_BOOST = 65.0     # InfraIsolateAndRegenerate
READMIT_THRESHOLD  = 70.0

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

class YunusScanRequest(BaseModel):
    text:      str
    stage:     int   = Field(5,   ge=0, le=9)
    coherence: float = Field(5.0, ge=0, le=10)

class AddHoldingRequest(BaseModel):
    ticker:   str
    shares:   float = Field(10.0, gt=0)
    avg_cost: float = Field(0.0,  ge=0)

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
    """LuminarkTrajectoryState for the portfolio domain."""

    def __init__(self) -> None:
        self.snapshots:       List[PortfolioSnapshot] = []
        self.last_stable:     Optional[PortfolioSnapshot] = None
        self.harrowing_active: bool = False

    def record(self, snap: PortfolioSnapshot) -> None:
        self.snapshots.append(snap)
        # Auto-preserve last stable snapshot (Stage 4-6, TrapScore < 0.5)
        if 4 <= snap.portfolio_stage <= 6 and snap.trap_score < 0.5:
            self.last_stable = snap
        self.harrowing_active = snap.trap_score > 0.80 or snap.portfolio_stage <= 2

    def get_metrics(self) -> Dict:
        n = len(self.snapshots)
        base = {
            "sample_count":      n,
            "harrowing_active":  self.harrowing_active,
            "last_stable_stage": self.last_stable.portfolio_stage if self.last_stable else None,
            "last_stable_at":    (datetime.fromtimestamp(self.last_stable.timestamp)
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

    # ── False Light detection ─────────────────────────────────────────────────
    def detect_false_light(self, stage: int, dims: Dict, trap_score: float) -> bool:
        if stage >= 8 and dims["coherence"] < 3.0:
            return True
        if stage >= 7 and trap_score > 0.72:
            return True
        return False

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

        false_light       = self.detect_false_light(stage, dims, trap_score)
        reroute_suggested = stage <= 2
        reroute_pct       = int(REROUTE_FRACTION * 100) if reroute_suggested else 0

        cur   = data["price"]
        cost  = h.avg_cost if h.avg_cost > 0 else round(cur * 0.88, 2)
        value = round(cur * h.shares, 2)
        pnl   = round((cur - cost) / cost * 100, 2)

        if false_light:
            desc = (f"⚠️ FALSE LIGHT — Stage {stage} surface stability is deceptive. "
                    "Coherence collapse risk. Recommend re-evaluation at Stage 5.")
        elif stage <= 2:
            desc = (f"🔴 CRITICAL — {SAP_DESCRIPTIONS[stage]} "
                    f"InfraAdaptiveCamouflage recommends rerouting {reroute_pct}% "
                    "to healthier positions.")
        elif stage == 8:
            desc = (f"⚡ BRITTLE PEAK — TrapScore {trap_score:.2f}. "
                    "High coherence masking brittleness. Monitor closely.")
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
            desc = (f"⚠️ FALSE LIGHT — Trader at Stage {stage} showing brittle "
                    "overconfidence patterns. Humility intervention recommended.")
        elif trap_risk:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    f"TrapScore {trap_score:.2f}. Review risk management discipline.")
        elif stage >= 6:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    "Disciplined execution with healthy risk management.")
        else:
            desc = (f"Behavioral stage {stage} — {archetype}. "
                    "Room for improvement in key behavioral metrics.")

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

    # ── Yunus Protocol ────────────────────────────────────────────────────────
    def yunus_scan(self, text: str, stage: int = 5, coherence: float = 5.0) -> Dict:
        tl = text.lower()
        detected = [m for m in YUNUS_ARROGANCE_MARKERS if m in tl]

        score = max(0, 100 - len(detected) * 14)
        flags = []
        if len(detected) >= 2:
            flags.append("YUNUS_STAGE8_TRAP")
        if any(m in tl for m in ["no risk", "can't lose", "100% profit", "risk free"]):
            flags.append("YUNUS_NO_WORST_CASE")

        # False Light check
        false_light = stage >= 8 and coherence < 3.0
        if false_light:
            flags.append("FALSE_LIGHT_DETECTED")
            score = min(score, 35)

        output_safe = score >= 70 and not false_light

        if false_light:
            rec = ("FALSE LIGHT DETECTED: Collapse stage assessment to Stage 5. "
                   "Surface confidence is not supported by underlying coherence.")
        elif "YUNUS_STAGE8_TRAP" in flags:
            rec = (f"COMPASSIONATE CONTAINMENT: Reduce position sizes 30-40%. "
                   f"Markers detected: {', '.join(detected[:3])}. "
                   "Worst-case scenario has not been accounted for.")
        elif detected:
            rec = (f"Overconfidence signals found: {', '.join(detected[:2])}. "
                   "Re-examine risk assumptions before executing.")
        else:
            rec = "Epistemic humility maintained. Trading notes appear grounded."

        return {
            "output_safe":       output_safe,
            "yunus_score":       round(score, 1),
            "detected_markers":  detected,
            "flags":             flags,
            "false_light":       false_light,
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
    title="ANUBIS — LUMINARK Portfolio Intelligence",
    description=(
        "SAP 10-stage portfolio classification, trajectory tracking, "
        "Yunus epistemic safety, and Harrowing recovery — powered by LUMINARK."
    ),
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine  = AnubisEngine()
session = SessionTrajectory()

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status":    "operational",
        "version":   "2.0.0",
        "yfinance":  YFINANCE_AVAILABLE,
        "real_data": YFINANCE_AVAILABLE,
        "snapshots": len(session.snapshots),
    }

@app.get("/api/portfolio/demo")
async def demo_portfolio():
    return {"holdings": DEMO_PORTFOLIO, "message": "Demo portfolio loaded — 6 holdings"}

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
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

    # Harrowing Protocol
    harrowing = {
        "active":             session.harrowing_active,
        "last_stable_stage":  (session.last_stable.portfolio_stage
                               if session.last_stable else None),
        "last_stable_at":     (datetime.fromtimestamp(session.last_stable.timestamp)
                               .strftime("%Y-%m-%d %H:%M")
                               if session.last_stable else None),
        "restoration_action": (
            f"SHADOW_RETRIEVAL: Restore toward Stage "
            f"{session.last_stable.portfolio_stage} — reduce high-TrapScore positions "
            "and increase allocation to Stage 5-6 holdings."
            if session.last_stable else
            "No stable baseline recorded yet. Run multiple analyses to build one."
        ),
        "quarantine_risk":    portfolio_trap > 0.90 or portfolio_stage <= 1,
        "mode": (
            "QUARANTINE"  if portfolio_trap > 0.90 or portfolio_stage <= 1 else
            "HARROWING"   if session.harrowing_active else
            "NORMAL"
        ),
    }

    # Threats
    threats = []
    for h in analyzed:
        if h["false_light"]:
            threats.append({"ticker": h["ticker"], "severity": "HIGH",
                            "type": "FALSE_LIGHT",
                            "description": f"FALSE LIGHT: Stage {h['stage']} — coherence collapse imminent"})
        elif h["stage"] <= 2:
            threats.append({"ticker": h["ticker"], "severity": "CRITICAL",
                            "type": "CRITICAL_STAGE",
                            "description": f"Stage {h['stage']} — critical deterioration active"})
        elif h["trap_score"] > 0.65:
            threats.append({"ticker": h["ticker"], "severity": "MEDIUM",
                            "type": "TRAP_RISK",
                            "description": f"TrapScore {h['trap_score']:.2f} — brittle peak risk"})

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
async def yunus_scan(req: YunusScanRequest):
    return engine.yunus_scan(req.text, req.stage, req.coherence)

@app.get("/api/harrowing_status")
async def harrowing_status():
    return {
        "active":            session.harrowing_active,
        "mode":              ("QUARANTINE" if
                              session.snapshots and session.snapshots[-1].trap_score > 0.90
                              else "HARROWING" if session.harrowing_active else "NORMAL"),
        "last_stable_stage": (session.last_stable.portfolio_stage
                              if session.last_stable else None),
        "last_stable_at":    (datetime.fromtimestamp(session.last_stable.timestamp)
                              .strftime("%Y-%m-%d %H:%M")
                              if session.last_stable else None),
        "snapshots_recorded": len(session.snapshots),
        "quarantine_risk":    (session.snapshots[-1].trap_score > 0.90
                               if session.snapshots else False),
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
