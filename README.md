# ⚡ AI-Based Smart Home Energy Management

> **Autonomous Appliance State Search, Symbolic Energy Reasoning, Multi-Agent System (MAS) Coordination, Modern AI Paradigms & Explainable Generative Assistant**

An end-to-end, runnable smart home energy planner built with Python and Streamlit. The system combines classical state-space search (A*, CSP), symbolic forward-chaining expert systems, distributed multi-agent coordination, predictive load analysis, and an explainable generative assistant grounded in physical telemetry.

---

## ✨ System Capabilities

| Module | Core AI Paradigm | Key Capability |
|---|---|---|
| **🏠 Energy Dashboard** | Hybrid Supervisory | Live 24h power dispatch visualization (Solar, BESS, Baseload, Grid, TOU Tariffs). |
| **🔍 Appliance Search** | State-Space Graph Search (A*, CSP) | Optimal start-time scheduling minimizing TOU bills and peak breaker load within user deadlines. |
| **📋 Symbolic Rule Engine** | Forward-Chaining Expert System | 100% deterministic safety overrides, battery reserve protection, and peak curtailment rules. |
| **🤖 Multi-Agent Control** | Distributed Multi-Agent System (MAS) | 5 collaborative sub-agents (Grid, Storage, Climate, Loads, Coordinator) with FIPA message logs. |
| **📊 AI Paradigms** | Comparative AI & Task Recommender | In-depth trade-off matrix comparing 6 AI paradigms with an interactive task selector. |
| **💬 Explainable Assistant** | Generative AI & RAG Grounding | Conversational assistant explaining automated energy decisions citing telemetry and active rules. |
| **⚙️ Simulation & Eval** | Quantitative Benchmark Suite | Multi-scenario evaluation across Summer, Winter, and Emergency Demand-Response profiles. |

---

## 🏗️ Multi-Layered AI Architecture

```
┌────────────────────────────────────────────────────────┐
│  Generative AI Layer (Explainable Resident Assistant)  │
├────────────────────────────────────────────────────────┤
│  Multi-Agent Coordination Layer (Decentralized MAS)    │
│  [Grid] ⇆ [Solar/Storage] ⇆ [Climate] ⇆ [Loads]       │
│                     ⇅                                  │
│             [Coordinator Agent]                        │
├────────────────────────────────────────────────────────┤
│  Planning Layer (A* State-Space Shift-Scheduling & CSP)│
├────────────────────────────────────────────────────────┤
│  Safety Shield (Symbolic Forward-Chaining Rules)       │
│  [Peak Curtailment] [Reserve Floor] [Comfort Override] │
├────────────────────────────────────────────────────────┤
│  Physical Plant: Solar Inverter, 10 kWh BESS, Breaker  │
└────────────────────────────────────────────────────────┘
```

---

## 📐 Algorithmic Formulation

### 1. A* State-Space Search & Admissible Heuristic
- **State Space:** Vector of assigned appliance start-times $s = \{(a_1, t_1), (a_2, t_2), \dots, (a_k, t_k)\}$.
- **Evaluation Function:** $f(s) = g(s) + h(s)$
  - $g(s)$: Exact electricity purchase cost plus comfort penalties accumulated by assigned appliances.
  - $h(s)$: Admissible lower bound computed as the remaining unscheduled appliance energy multiplied by the daily minimum tariff $T_{\min}$:
    $$h(s) = \sum_{j=k+1}^N \left(\text{Power}_j \times \text{Duration}_j\right) \cdot \min_{t} \text{Tariff}(t)$$
  - Because $h(s) \le h^*(s)$, search optimality is mathematically guaranteed.

### 2. Constraint-Satisfaction Problem (CSP)
- Enforces hard physical service limits: $\text{Peak Load}(t) \le P_{\max}$ (e.g. $10.0\text{ kW}$ main breaker capacity) to prevent circuit breaker trips.

### 3. Symbolic Energy Production Rules (IF-THEN)
- **R01 (Peak Load Curtailment):** If tariff $\ge \$0.40/\text{kWh}$, defer flexible loads (Priority $\ge 3$).
- **R02 (Solar Self-Consumption):** Divert midday solar surplus ($> 1.0\text{ kW}$) to charge battery or pre-cool home.
- **R03 (Battery Peak Arbitrage):** Discharge battery during 16:00–21:00 peak hours to eliminate expensive grid draw.
- **R04 (Emergency Reserve Floor):** Inhibit discharge once battery State-of-Charge reaches $20\%$ ($2.0\text{ kWh}$) reserve.
- **R06 (Demand Response Curtailment):** Throttle non-critical loads during utility critical peak emergencies ($\$1.25/\text{kWh}$).
- **R07 (Thermal Comfort Safety):** Engage HVAC whenever indoor temperature drifts outside $[18^\circ\text{C}, 26^\circ\text{C}]$, overriding economic optimization.

### 4. Distributed Multi-Agent System (MAS)
- **Agents:** Grid Monitor, Solar & Storage, Climate & HVAC, Flexible Loads, and Central Coordinator.
- **Communicative Acts:** Standardized FIPA performatives (`INFORM`, `REQUEST`, `PROPOSE`, `ACCEPT`, `REJECT`, `CONFIRM`).
- **Negotiation:** When aggregate home power exceeds breaker thresholds, the Coordinator executes an automated priority auction to curtail or throttle discretionary loads.

---

## 🚀 Installation & Local Execution (Windows)

### 1. Clone & Activate Virtual Environment
```powershell
cd "c:\Users\vivek\Downloads\ai project"
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Run the Unit Test Suite
```powershell
python -m pytest tests/test_smart_home.py -v
```
*(All 18 unit tests cover models, search algorithms, rule engines, multi-agent coordination, and assistant fallback).*

### 4. Launch the Streamlit Web Application
```powershell
streamlit run app.py
```
Open your browser to: **[http://localhost:8501](http://localhost:8501)**.

---

## 🔑 Optional OpenAI Configuration

The application operates **100% offline** with zero API costs using a deterministic explainable synthesis engine grounded in factual telemetry.

To enable generative explanations powered by OpenAI:
1. Open the `.env` file in the project root.
2. Configure:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-actual-api-key-here
   OPENAI_MODEL=gpt-3.5-turbo
   ```
3. Save and refresh the Streamlit app.
*(Secrets are strictly isolated in `.env` and excluded from git by `.gitignore`)*.
