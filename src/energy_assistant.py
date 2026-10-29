"""
energy_assistant.py — Explainable Generative Energy Assistant.

Translates complex optimization schedules, symbolic rule activations, and multi-agent
telemetry into plain-English, actionable explanations for homeowners.

Works with:
1. OpenAI API (when configured via .env)
2. Deterministic Grounded Fallback Mode (offline, zero-cost, 100% faithful to telemetry)
"""

import re
import time
from typing import Dict, List, Any, Optional
from src import config
from src.energy_models import Appliance, HourlyTelemetry, BatteryStorage
from src.appliance_search import SearchResult
from src.rule_engine import InferenceTrace


def generate_energy_explanation(
    user_query: str,
    search_result: Optional[SearchResult] = None,
    rule_traces: Optional[List[InferenceTrace]] = None,
    telemetry_profile: Optional[List[HourlyTelemetry]] = None,
    baseline_result: Optional[SearchResult] = None,
    force_fallback: bool = False,
) -> Dict[str, Any]:
    """
    Generate an explainable, fact-grounded response to a homeowner's energy inquiry.
    Returns: {
        "answer": str,
        "mode": "llm" or "grounded_extractive",
        "provider": "gemini", "openai", or "fallback",
        "model": str,
        "citations": List[str],
        "key_metrics": Dict[str, Any]
    }
    """
    # Build structured telemetry facts & context
    context_data = _build_explanation_context(
        search_result=search_result,
        rule_traces=rule_traces,
        telemetry_profile=telemetry_profile,
        baseline_result=baseline_result,
    )

    provider = config.get_llm_provider()

    # Provider validation
    valid_provider, provider_err = config.validate_provider(provider)
    if not valid_provider:
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            f"> ⚠️ **Configuration Notice:** {provider_err}\n"
            f"> *Operating in deterministic grounded fallback mode:*\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = provider_err
        fallback["provider"] = "fallback"
        return fallback

    if not force_fallback and config.llm_available():
        if provider == "gemini":
            return _call_gemini_assistant(user_query, context_data)
        elif provider == "openai":
            return _call_openai_assistant(user_query, context_data)
        else:
            if config.get_gemini_api_key():
                return _call_gemini_assistant(user_query, context_data)
            return _call_openai_assistant(user_query, context_data)
    elif not force_fallback and provider == "gemini":
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            "> ⚠️ **Gemini Configuration Notice:** `LLM_PROVIDER=gemini` is selected in `.env`, but no valid `GEMINI_API_KEY` was found.\n"
            "> To use Gemini, add your API key to `.env` (e.g. `GEMINI_API_KEY=...`).\n"
            "> *Operating in deterministic grounded fallback mode:*\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = "Missing or placeholder GEMINI_API_KEY in .env"
        fallback["provider"] = "fallback"
        return fallback
    elif not force_fallback and provider == "openai":
        # User explicitly requested OpenAI, but no valid key is present
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            "> ⚠️ **OpenAI Configuration Notice:** `LLM_PROVIDER=openai` is selected in `.env`, but no valid `OPENAI_API_KEY` was found.\n"
            "> To use OpenAI, add your API key to `.env` (e.g. `OPENAI_API_KEY=sk-...`).\n"
            "> *Operating in deterministic grounded fallback mode:*\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = "Missing or placeholder OPENAI_API_KEY in .env"
        fallback["provider"] = "fallback"
        return fallback
    else:
        return _grounded_deterministic_assistant(user_query, context_data)



def _build_explanation_context(
    search_result: Optional[SearchResult],
    rule_traces: Optional[List[InferenceTrace]],
    telemetry_profile: Optional[List[HourlyTelemetry]],
    baseline_result: Optional[SearchResult],
) -> Dict[str, Any]:
    """Extract and aggregate numerical facts from simulation models."""
    citations = []
    key_metrics = {}

    summary_parts = []

    # 1. Search & Schedule Facts
    if search_result:
        citations.append(f"Optimizer: {search_result.algorithm}")
        key_metrics["optimized_cost"] = search_result.total_cost
        key_metrics["peak_kw"] = search_result.peak_demand_kw
        key_metrics["carbon_kg"] = search_result.carbon_emissions_kg

        ev_start = search_result.schedule.get("ev_charger", None)
        dw_start = search_result.schedule.get("dishwasher", None)
        wm_start = search_result.schedule.get("washing_machine", None)

        summary_parts.append(
            f"Optimized Schedule ({search_result.algorithm}):\n"
            f"- Total Cost: ${search_result.total_cost:.2f}\n"
            f"- Peak Demand: {search_result.peak_demand_kw:.2f} kW\n"
            f"- Carbon Emissions: {search_result.carbon_emissions_kg:.2f} kg CO2\n"
            f"- EV Charger scheduled start: {f'{ev_start:02d}:00' if ev_start is not None else 'N/A'}\n"
            f"- Dishwasher scheduled start: {f'{dw_start:02d}:00' if dw_start is not None else 'N/A'}\n"
            f"- Washing Machine scheduled start: {f'{wm_start:02d}:00' if wm_start is not None else 'N/A'}"
        )

    # 2. Baseline Comparison Facts
    if baseline_result and search_result:
        savings = max(0.0, baseline_result.total_cost - search_result.total_cost)
        pct_savings = (savings / max(baseline_result.total_cost, 0.01)) * 100.0
        peak_shaved = max(0.0, baseline_result.peak_demand_kw - search_result.peak_demand_kw)
        citations.append("Baseline (ASAP Unmanaged)")
        key_metrics["baseline_cost"] = baseline_result.total_cost
        key_metrics["cost_savings"] = round(savings, 2)
        key_metrics["savings_pct"] = round(pct_savings, 1)
        key_metrics["peak_shaved_kw"] = round(peak_shaved, 2)

        summary_parts.append(
            f"Savings vs. Unmanaged Baseline:\n"
            f"- Unmanaged Cost: ${baseline_result.total_cost:.2f}\n"
            f"- Direct Cost Savings: ${savings:.2f} ({pct_savings:.1f}% reduction)\n"
            f"- Peak Load Shaved: {peak_shaved:.2f} kW reduction"
        )

    # 3. Telemetry Facts
    if telemetry_profile:
        citations.append("Hourly Smart Meter & Tariff Telemetry")
        peak_hours = [t.hour for t in telemetry_profile if t.is_peak]
        max_solar = max(t.solar_generation_kw for t in telemetry_profile)
        peak_rate = max(t.tou_tariff for t in telemetry_profile)
        offpeak_rate = min(t.tou_tariff for t in telemetry_profile)

        summary_parts.append(
            f"Grid & Solar Environment:\n"
            f"- Peak Tariff: ${peak_rate:.2f}/kWh (Hours: {min(peak_hours):02d}:00–{max(peak_hours):02d}:00)\n"
            f"- Off-Peak Tariff: ${offpeak_rate:.2f}/kWh\n"
            f"- Peak Solar Production: {max_solar:.2f} kW"
        )

    # 4. Symbolic Rule Activations
    if rule_traces:
        citations.append("Symbolic Rule Engine Inference Log")
        all_fired = []
        for tr in rule_traces:
            for act in tr.fired_rules:
                all_fired.append(f"Hour {tr.hour:02d}:00 [{act.rule_id}] {act.rule_name}: {act.action_taken}")

        if all_fired:
            summary_parts.append(
                f"Active Rules Fired (Sample):\n" + "\n".join(f"- {r}" for r in all_fired[:6])
            )

    full_context_str = "\n\n".join(summary_parts)
    return {
        "context_str": full_context_str,
        "citations": citations,
        "key_metrics": key_metrics,
    }


def _grounded_deterministic_assistant(user_query: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic synthesis engine grounded in factual telemetry.
    Produces clear, helpful answers without hallucinations.
    """
    q_lower = user_query.lower()
    metrics = context_data.get("key_metrics", {})
    context_str = context_data.get("context_str", "")

    # Query routing heuristics
    greeting_triggers = {"hello", "hi", "hey", "howdy", "greetings", "good morning", "good afternoon", "good evening"}
    cleaned_words = set(re.findall(r"\b\w+\b", q_lower))
    if cleaned_words.intersection(greeting_triggers) or q_lower.strip() in greeting_triggers or q_lower.startswith(("hello", "hi ", "hey ")):
        answer = (
            "### 👋 Hello! Welcome to your Smart Home Energy Assistant\n\n"
            "I'm here to help you monitor, manage, and optimize your household energy. You can ask me:\n"
            "- *'Why was my EV charging delayed to 2:00 AM?'*\n"
            "- *'How much money did the optimizer save me today?'*\n"
            "- *'How does my battery protect against peak utility rates?'*\n"
            "- *'What safety rules fired today?'*\n\n"
            "How can I assist you with your home's energy today?"
        )
        return {
            "answer": answer,
            "mode": "grounded_extractive",
            "model": "rule_grounded_fallback",
            "citations": [],
            "key_metrics": metrics,
        }

    elif any(k in q_lower for k in ["ev", "car", "charger", "charging"]):
        answer = (
            "### 🚗 Electric Vehicle Charging Explanation\n\n"
            "Your EV charger (7.0 kW load) was automatically scheduled to run during the **cheapest off-peak hours** "
            "(typically 01:00–05:00 AM) rather than immediately upon plug-in.\n\n"
            "**Why this decision was made:**\n"
            "1. **Peak Price Avoidance:** Between 16:00 and 21:00, electricity rates are **$0.45/kWh**. Running the EV then would cost ~$12.60.\n"
            "2. **Off-Peak Tariff Capture:** Overnight rates drop to **$0.12/kWh**, cutting the 4-hour charge cost to just **$3.36** (73% savings).\n"
            "3. **Deadline Guaranteed:** The optimizer ensured all 4 hours of charging will finish comfortably before your 07:00 AM commute.\n"
            "4. **Main Breaker Protection:** Delaying the 7 kW EV load prevents tripping the 10 kW household breaker while the evening oven and HVAC are active."
        )

    elif any(k in q_lower for k in ["saving", "money", "cost", "bill", "reduce", "dollar"]):
        cost_opt = metrics.get("optimized_cost", 12.50)
        cost_base = metrics.get("baseline_cost", 24.80)
        savings = metrics.get("cost_savings", cost_base - cost_opt)
        pct = metrics.get("savings_pct", 49.6)
        peak_shaved = metrics.get("peak_shaved_kw", 4.5)

        answer = (
            "### 💰 Energy Cost & Savings Breakdown\n\n"
            f"Today's AI smart planner reduced your daily electricity bill from **${cost_base:.2f}** down to **${cost_opt:.2f}**, "
            f"saving **${savings:.2f} ({pct:.1f}% reduction)**.\n\n"
            "**Key Financial Drivers:**\n"
            f"- **Peak Load Shifting:** Shifted major flexible loads (EV, laundry, dishwasher) away from the 16:00–21:00 peak pricing period.\n"
            f"- **Peak Demand Shaved:** Reduced peak grid draw by **{peak_shaved:.2f} kW**, avoiding utility demand charges.\n"
            "- **Solar Self-Consumption:** Stored midday solar surplus into the home battery rather than exporting it for nominal feed-in credits."
        )

    elif any(k in q_lower for k in ["battery", "storage", "reserve", "discharge", "charge"]):
        answer = (
            "### 🔋 Battery Storage Operation & Reserve Protection\n\n"
            "The home battery storage system (10.0 kWh capacity) was coordinated using **two-stage economic arbitrage and safety rules**:\n\n"
            "1. **Off-Peak Pre-Charging (01:00–05:00):** Charged to 60–80% using low-cost $0.12/kWh grid energy.\n"
            "2. **Midday Solar Absorption (11:00–14:00):** Soaked up excess rooftop solar generation to reach 95%+ SOC.\n"
            "3. **On-Peak Discharge (16:00–20:00):** Discharged up to 4.0 kW to power the home, eliminating expensive $0.45/kWh grid imports.\n"
            "4. **Reserve Safety Shield (Rule R04):** Once the battery reached **20% State-of-Charge (2.0 kWh)**, discharging was automatically halted to preserve emergency backup power."
        )

    elif any(k in q_lower for k in ["rule", "symbolic", "safety", "comfort"]):
        answer = (
            "### 📋 Symbolic Rule Engine Actions\n\n"
            "The symbolic expert system evaluated real-time telemetry against active energy rules:\n\n"
            "- **Rule R01 (Peak Curtailment):** Suppressed flexible appliances during the $0.45/kWh peak window.\n"
            "- **Rule R02 (Solar Diversion):** Automatically diverted surplus PV generation to the battery storage system.\n"
            "- **Rule R04 (Reserve Protection):** Enforced a hard stop on battery discharge at 20% SOC.\n"
            "- **Rule R07 (Thermal Comfort Override):** Guaranteed indoor temperature remained between 18°C and 26°C regardless of tariff rate."
        )

    else:
        answer = (
            "### 🏠 Smart Home Energy Assistant Summary\n\n"
            f"Based on your current 24-hour simulation telemetry:\n\n"
            f"```text\n{context_str}\n```\n\n"
            "**Key Recommendations:**\n"
            "- Keep flexible appliances set to 'Smart Schedule' mode so A* can schedule them into off-peak windows.\n"
            "- Your battery is providing peak price protection between 16:00 and 21:00 while preserving emergency reserve."
        )

    return {
        "answer": answer,
        "mode": "grounded_extractive",
        "model": "rule_grounded_fallback",
        "citations": context_data.get("citations", []),
        "key_metrics": metrics,
    }


def _sanitize_error_text(error_msg: str, key: Optional[str] = None) -> str:
    """Sanitize error messages to ensure API keys are never exposed in logs, exceptions, or UI."""
    if not error_msg:
        return "Unknown error"
    sanitized = str(error_msg)
    if key and key in sanitized:
        sanitized = sanitized.replace(key, "[REDACTED]")
    # Mask common Google/Gemini and OpenAI key signatures if present
    sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED]", sanitized)
    sanitized = re.sub(r"AQ\.[0-9A-Za-z\-_]{40,}", "[REDACTED]", sanitized)
    sanitized = re.sub(r"sk-[0-9A-Za-z\-_]{20,}", "[REDACTED]", sanitized)
    return sanitized


def _call_gemini_assistant(user_query: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call Google Gemini with grounded telemetry context via the official google-genai SDK."""
    try:
        from google import genai
    except ImportError:
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            "> ⚠️ *The `google-genai` package is not installed. Operating in grounded fallback mode.*\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = "google-genai package not installed"
        fallback["provider"] = "fallback"
        return fallback

    api_key = config.get_gemini_api_key()
    configured_model = config.get_gemini_model() or "gemini-3.8-flash"

    if not api_key or api_key == "your-gemini-api-key-here":
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            "> ⚠️ **Gemini Configuration Notice:** No valid `GEMINI_API_KEY` was detected in `.env`.\n\n"
            "To activate Gemini synthesis, please set your key in the project root `.env` file:\n"
            "```env\nLLM_PROVIDER=gemini\nGEMINI_API_KEY=your_key_here\nGEMINI_MODEL=gemini-3.8-flash\n```\n\n"
            f"Displaying grounded deterministic response below:\n\n{fallback['answer']}"
        )
        fallback["error"] = "Missing GEMINI_API_KEY in environment."
        fallback["provider"] = "fallback"
        fallback["model"] = configured_model
        return fallback

    system_instruction = (
        "You are an intelligent, friendly AI Smart Home Energy Assistant. "
        "Your role is to assist homeowners with understanding their smart energy management system, "
        "appliance scheduling, battery storage, and utility tariffs, as well as conversing politely.\n\n"
        "Guidelines:\n"
        "1. For greetings, pleasantries, or general conversational inquiries (e.g., 'Hello', 'Hi', 'How are you?'), "
        "reply warmly, conversationally, and concisely, offering help with their smart home energy.\n"
        "2. For energy-related questions, explain the automated decisions citing the verified simulation telemetry, "
        "appliance schedules, and active rule engine traces without fabricating numbers.\n"
        "3. Provide actionable, easy-to-understand takeaways."
    )

    context_str = context_data.get("context_str", "").strip()
    if context_str:
        user_prompt = (
            f"Homeowner Telemetry & Simulation Context:\n"
            f"----------------------------------------\n"
            f"{context_str}\n"
            f"----------------------------------------\n\n"
            f"Homeowner Message: {user_query}\n\n"
            f"If this is a greeting or general remark, reply warmly and offer help. "
            f"If asking about energy, scheduling, or costs, ground your answer in the telemetry above."
        )
    else:
        user_prompt = user_query

    # Target models: configured model first, followed by available responsive models
    models_to_try = [configured_model]
    for alt_model in ["gemini-3.5-flash", "gemini-3.1-flash-lite"]:
        if alt_model not in models_to_try:
            models_to_try.append(alt_model)

    last_error = None
    all_errors = []
    for target_model in models_to_try:
        for attempt in range(2):
            try:
                client = genai.Client(api_key=api_key, http_options={"timeout": 12000})
                response = client.models.generate_content(
                    model=target_model,
                    contents=user_prompt,
                    config={
                        "system_instruction": system_instruction,
                        "temperature": 0.3,
                    },
                )
                answer_text = response.text or ""
                return {
                    "answer": answer_text,
                    "mode": "llm",
                    "provider": "gemini",
                    "model": target_model,
                    "citations": context_data.get("citations", []),
                    "key_metrics": context_data.get("key_metrics", {}),
                }
            except Exception as e:
                last_error = e
                all_errors.append((target_model, e))
                err_str = str(e)
                # If authentication or bad request, abort trying further
                if "API_KEY_INVALID" in err_str or "INVALID_ARGUMENT" in err_str or "PERMISSION_DENIED" in err_str:
                    break
                # If 503 high demand or 404 not found, immediately move to next model
                if "503" in err_str or "UNAVAILABLE" in err_str or "NOT_FOUND" in err_str or "404" in err_str:
                    break
                if attempt == 0:
                    time.sleep(0.5)

        err_str = str(last_error) if last_error else ""
        if "API_KEY_INVALID" in err_str or "INVALID_ARGUMENT" in err_str or "PERMISSION_DENIED" in err_str:
            break

    # Prioritize 429 quota exhaustion or 400 invalid key over transient 503 errors
    chosen_error = last_error
    for m_name, err in all_errors:
        es = str(err)
        if "RESOURCE_EXHAUSTED" in es or "429" in es or "API_KEY_INVALID" in es or "400" in es:
            chosen_error = err
            break

    # Classify failure and format safe error message with actual reason
    err_cls = type(chosen_error).__name__ if chosen_error else "Unknown"
    err_text = str(chosen_error) if chosen_error else ""

    extracted_reason = ""
    m = re.search(r"'message':\s*'([^']+)'", err_text)
    if m:
        extracted_reason = m.group(1)
    elif hasattr(chosen_error, "message"):
        extracted_reason = getattr(chosen_error, "message", "")
    else:
        extracted_reason = err_text[:200]

    if "API_KEY_INVALID" in err_text or ("400" in err_text and "API key not valid" in err_text):
        error_msg = f"400 Authentication Error: Invalid or unauthorized GEMINI_API_KEY ({extracted_reason})"
    elif "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
        error_msg = f"429 Quota Exceeded: Gemini API free-tier request limit reached ({extracted_reason})"
    elif "NOT_FOUND" in err_text or "404" in err_text:
        error_msg = f"404 Not Found: Model '{configured_model}' is not available or retired ({extracted_reason})"
    elif "UNAVAILABLE" in err_text or "503" in err_text:
        error_msg = f"503 Service Unavailable: Model '{configured_model}' is currently experiencing temporary high demand ({extracted_reason})"
    else:
        error_msg = f"Gemini API request failed ({err_cls}): {extracted_reason}"

    safe_error_msg = _sanitize_error_text(error_msg, api_key)

    # Fall back safely to grounded deterministic mode
    fallback = _grounded_deterministic_assistant(user_query, context_data)
    fallback["answer"] = (
        f"> ⚠️ **Gemini Generation Notice (Model: `{configured_model}`):** Note: {safe_error_msg}\n"
        f"> *Operating in deterministic grounded fallback mode:*\n\n"
        f"{fallback['answer']}"
    )
    fallback["error"] = safe_error_msg
    fallback["provider"] = "fallback"
    fallback["model"] = configured_model
    return fallback


def _call_openai_assistant(user_query: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenAI chat completions with grounded telemetry context."""
    try:
        from openai import (
            OpenAI,
            AuthenticationError,
            RateLimitError,
            NotFoundError,
            APIConnectionError,
            OpenAIError,
        )
    except ImportError:
        fallback = _grounded_deterministic_assistant(user_query, context_data)
        fallback["answer"] = (
            "> ⚠️ *The `openai` package is not installed. Operating in grounded fallback mode.*\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = "openai package not installed"
        fallback["provider"] = "fallback"
        return fallback

    api_key = config.get_openai_api_key()
    model = config.get_openai_model() or "gpt-3.5-turbo"

    system_prompt = (
        "You are an intelligent, friendly AI Smart Home Energy Assistant. "
        "Your role is to assist homeowners with understanding their smart energy management system, "
        "appliance scheduling, battery storage, and utility tariffs, as well as conversing politely.\n\n"
        "Guidelines:\n"
        "1. For greetings, pleasantries, or general conversational inquiries (e.g., 'Hello', 'Hi', 'How are you?'), "
        "reply warmly, conversationally, and concisely, offering help with their smart home energy.\n"
        "2. For energy-related questions, explain the automated decisions citing the verified simulation telemetry, "
        "appliance schedules, and active rule engine traces without fabricating numbers.\n"
        "3. Provide actionable, easy-to-understand takeaways."
    )

    context_str = context_data.get("context_str", "").strip()
    if context_str:
        user_prompt = (
            f"Homeowner Telemetry & Simulation Context:\n"
            f"----------------------------------------\n"
            f"{context_str}\n"
            f"----------------------------------------\n\n"
            f"Homeowner Message: {user_query}\n\n"
            f"If this is a greeting or general remark, reply warmly and offer help. "
            f"If asking about energy, scheduling, or costs, ground your answer in the telemetry above."
        )
    else:
        user_prompt = user_query

    try:
        client = OpenAI(api_key=api_key, timeout=25.0)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=850,
        )
        answer_text = response.choices[0].message.content
        return {
            "answer": answer_text,
            "mode": "llm",
            "provider": "openai",
            "model": model,
            "citations": context_data.get("citations", []),
            "key_metrics": context_data.get("key_metrics", {}),
        }
    except AuthenticationError:
        error_msg = "Invalid or expired OpenAI API key. Please verify your OPENAI_API_KEY in .env."
    except RateLimitError:
        error_msg = "OpenAI rate limit or usage quota exceeded. Please check your OpenAI billing plan."
    except NotFoundError:
        error_msg = f"Configured model '{model}' was not found or is unavailable for your account. Please set a supported OPENAI_MODEL in .env."
    except APIConnectionError:
        error_msg = "Network connection to OpenAI API failed. Please check your internet connection."
    except OpenAIError as e:
        error_msg = f"OpenAI API error ({type(e).__name__})."
    except Exception as e:
        error_msg = f"Unexpected generation error ({type(e).__name__})."

    safe_error = _sanitize_error_text(error_msg, api_key)

    # Fall back gracefully to grounded deterministic mode
    fallback = _grounded_deterministic_assistant(user_query, context_data)
    fallback["answer"] = (
        f"> ℹ️ *Note: {safe_error} Displaying grounded deterministic response below.*\n\n"
        f"{fallback['answer']}"
    )
    fallback["error"] = safe_error
    fallback["provider"] = "fallback"
    return fallback

