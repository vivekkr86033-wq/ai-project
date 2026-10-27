"""
energy_paradigms.py — Comprehensive comparison of Modern AI Paradigms
for Smart Home Energy Management and Task-to-Paradigm Recommender.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class AIParadigm:
    id: str
    name: str
    category: str
    core_mechanism: str
    smart_home_application: str
    strengths: List[str]
    limitations: List[str]
    optimality: str             # High, Medium, Low
    latency: str                # Real-time (<10ms), Fast (<1s), Medium (<5s)
    interpretability: str       # High, Medium, Black-box
    safety_assurance: str       # Provable / Formal, Empirical, Stochastic
    sample_efficiency: str      # High (No training), Low (Data hungry)


ENERGY_AI_PARADIGMS: List[AIParadigm] = [
    AIParadigm(
        id="classical_search",
        name="Classical Search & Planning (A*, CSP)",
        category="State-Space Search",
        core_mechanism="Graph search evaluating f(n) = g(n) + h(n) with admissible heuristics and constraint propagation.",
        smart_home_application="Optimal scheduling of shiftable appliances (EV charger, laundry, dishwasher) to minimize TOU electricity costs while respecting deadlines and breaker power limits.",
        strengths=[
            "Guaranteed global or near-optimal cost minimization under known tariff horizons.",
            "Strict satisfaction of hard safety constraints (e.g. main breaker capacity ≤ 10 kW).",
            "Zero training data required; immediately usable upon parameter configuration.",
        ],
        limitations=[
            "Combinatorial state explosion with many concurrently shiftable devices.",
            "Requires deterministic forecasts of tariffs and appliance durations.",
        ],
        optimality="High",
        latency="Fast (<500ms)",
        interpretability="High (Full search path & cost breakdown)",
        safety_assurance="Provable constraint satisfaction",
        sample_efficiency="Very High (Zero-shot)",
    ),
    AIParadigm(
        id="symbolic_rules",
        name="Symbolic Production Rules & Expert Systems",
        category="Rule-Based Reasoning",
        core_mechanism="Forward-chaining inference engine matching current telemetry against condition-action production rules (IF-THEN).",
        smart_home_application="Safety overrides, battery emergency reserve cutoffs (min 20% SOC), utility demand-response curtailment, and thermal comfort safety limits.",
        strengths=[
            "100% deterministic, verifiable, and safety-compliant.",
            "Microsecond execution latency for critical physical protection.",
            "Directly explainable: every action traces to a named human-written rule.",
        ],
        limitations=[
            "Brittle when unmodeled environmental conditions occur.",
            "Cannot dynamically balance multi-objective continuous trade-offs.",
        ],
        optimality="Medium (Greedy heuristic execution)",
        latency="Real-time (<5ms)",
        interpretability="Highest (Human-readable logic)",
        safety_assurance="Formally verifiable",
        sample_efficiency="Highest (Domain-expert encoded)",
    ),
    AIParadigm(
        id="supervised_ml",
        name="Supervised Machine Learning (Forecasting)",
        category="Predictive ML",
        core_mechanism="Gradient Boosted Trees, Random Forests, and LSTMs trained on historical meteorological and smart meter telemetry.",
        smart_home_application="Predicting next-day rooftop solar PV generation profiles and uncontrollable household baseload power consumption curves.",
        strengths=[
            "Captures non-linear relationships between weather (cloud cover, temperature) and energy generation.",
            "Adapts to changing household occupancy habits over seasons.",
        ],
        limitations=[
            "Purely predictive: cannot take physical control actions on its own.",
            "Susceptible to distribution shifts (e.g. unpredicted snowstorm or holiday guest occupancy).",
        ],
        optimality="N/A (Prediction only)",
        latency="Fast (<100ms inference)",
        interpretability="Medium (Feature importances, SHAP values)",
        safety_assurance="Empirical / Statistical",
        sample_efficiency="Medium (Requires historical telemetry)",
    ),
    AIParadigm(
        id="reinforcement_learning",
        name="Reinforcement Learning / MDP (Dynamic Arbitrage)",
        category="Markov Decision Processes",
        core_mechanism="Policy optimization (Q-Learning / PPO) maximizing cumulative reward = -Cost - Discomfort over stochastic transitions.",
        smart_home_application="Continuous battery energy storage (BESS) charge/discharge dispatch under stochastic real-time electricity pricing and solar fluctuations.",
        strengths=[
            "Learns complex control policies without requiring exact mathematical transition equations.",
            "Optimizes multi-period sequential decisions under price volatility.",
        ],
        limitations=[
            "High sample complexity requiring thousands of simulated episodes.",
            "Exploration phase risks executing suboptimal or damaging physical actions unless constrained by safety shielding.",
        ],
        optimality="High (Asymptotically optimal)",
        latency="Real-time (<20ms policy forward pass)",
        interpretability="Low / Black-box (Neural policy weights)",
        safety_assurance="Empirical (Needs symbolic safety shield)",
        sample_efficiency="Low (Data intensive)",
    ),
    AIParadigm(
        id="multi_agent_systems",
        name="Multi-Agent Systems & Distributed Control",
        category="Distributed AI",
        core_mechanism="Specialized autonomous agents (Grid, Solar, Battery, HVAC, Loads) coordinating via FIPA communicative acts and local priority auctions.",
        smart_home_application="Decentralized home energy management where individual subsystems maintain privacy, negotiate breaker allocations, and avoid single points of failure.",
        strengths=[
            "Highly modular: new appliances can be plugged in as new agents dynamically.",
            "Preserves component autonomy and privacy across tenant sub-circuits.",
            "Resilient to partial system sensor failures.",
        ],
        limitations=[
            "Inter-agent messaging latency and potential communication bottlenecks.",
            "Decentralized equilibrium can be slightly suboptimal compared to monolithic centralized optimization.",
        ],
        optimality="Medium-High (Negotiated consensus)",
        latency="Medium (<1s negotiation rounds)",
        interpretability="High (Inter-agent communicative trace)",
        safety_assurance="High with coordinator arbiter",
        sample_efficiency="High (Modular logic)",
    ),
    AIParadigm(
        id="generative_ai",
        name="Generative AI & Explainable LLM Assistants",
        category="Explainable Foundation Models",
        core_mechanism="Large Language Models grounded via RAG and telemetry retrieval to synthesize contextual, transparent explanations and energy advice.",
        smart_home_application="Interactive conversational assistant explaining automated energy decisions (e.g. 'Why was my EV charging delayed?'), summarizing daily savings, and providing customized conservation tips.",
        strengths=[
            "Natural language interface accessible to non-technical homeowners.",
            "Synthesizes disparate telemetry, rules, and schedules into coherent explanations.",
            "Translates complex tariff mathematics into intuitive financial and environmental savings.",
        ],
        limitations=[
            "Higher computational latency and API costs.",
            "Unsuitable for high-speed sub-second physical device actuation.",
            "Requires grounded telemetry to avoid hallucinated energy metrics.",
        ],
        optimality="High for communication / N/A for physical actuation",
        latency="Medium (<2s response time)",
        interpretability="Highest (Plain English reasoning)",
        safety_assurance="High with deterministic grounding",
        sample_efficiency="High (Pre-trained foundation models)",
    ),
]


# ── Task Recommender ──────────────────────────────────────────

RECOMMENDED_TASKS: List[Dict[str, Any]] = [
    {
        "id": "T1",
        "task_name": "Appliance Shift-Scheduling with Deadlines",
        "description": "Schedule washing machines, EV charging, and dishwashers to minimize TOU bills before morning commute.",
        "recommended_paradigm": "classical_search",
        "rationale": "A* and CSP provide mathematically provable cost minimization while strictly guaranteeing hard user deadlines.",
        "alternative_paradigm": "multi_agent_systems",
    },
    {
        "id": "T2",
        "task_name": "Battery Outage Reserve & Safety Protection",
        "description": "Ensure home battery never drains below 20% to safeguard emergency power during storm warnings.",
        "recommended_paradigm": "symbolic_rules",
        "rationale": "Symbolic production rules are 100% deterministic and execute with zero latency, eliminating any black-box failure risk.",
        "alternative_paradigm": "classical_search",
    },
    {
        "id": "T3",
        "task_name": "Tomorrow's Solar PV Generation Forecasting",
        "description": "Predict 24-hour ahead solar energy generation curve based on weather forecast and historical patterns.",
        "recommended_paradigm": "supervised_ml",
        "rationale": "Supervised gradient-boosted models excel at capturing complex non-linear meteorological relationships from historical smart meter logs.",
        "alternative_paradigm": "reinforcement_learning",
    },
    {
        "id": "T4",
        "task_name": "Arbitrage Under Volatile Real-Time Tariffs",
        "description": "Continually adapt battery charge/discharge cycles in response to 5-minute dynamic wholesale spot prices.",
        "recommended_paradigm": "reinforcement_learning",
        "rationale": "Reinforcement learning optimizes sequential decision-making under stochastic price shocks without requiring exact analytic models.",
        "alternative_paradigm": "classical_search",
    },
    {
        "id": "T5",
        "task_name": "Multi-Appliance Peak Breaker Coordination",
        "description": "Coordinate EV, HVAC, heat pump, and laundry so total household draw never trips the 10 kW service main breaker.",
        "recommended_paradigm": "multi_agent_systems",
        "rationale": "Multi-agent priority arbitration enables distributed devices to dynamically negotiate power shares without central reconfiguration.",
        "alternative_paradigm": "classical_search",
    },
    {
        "id": "T6",
        "task_name": "Explaining Optimization Decisions to Homeowner",
        "description": "Answer user questions like 'Why did my EV charge at 2:00 AM instead of 6:00 PM?' in natural language.",
        "recommended_paradigm": "generative_ai",
        "rationale": "Generative LLM agents bridge raw telemetry and mathematical schedules into friendly, transparent human explanations.",
        "alternative_paradigm": "symbolic_rules",
    },
]


def get_paradigm_by_id(pid: str) -> Optional[AIParadigm]:
    for p in ENERGY_AI_PARADIGMS:
        if p.id == pid:
            return p
    return None


def get_recommendation_for_task(task_id: str) -> Optional[Dict[str, Any]]:
    for t in RECOMMENDED_TASKS:
        if t["id"] == task_id:
            return t
    return None
