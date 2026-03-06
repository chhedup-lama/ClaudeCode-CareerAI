from agents.base import client, MODEL, extract_json
from agents.research import run_research_agent
from agents.workforce_analytics import run_workforce_analytics_agent
from agents.financial_impact import run_financial_impact_agent
from agents.strategy import run_strategy_agent
from agents.report_generator import run_report_generator_agent
from tools.data_loader import check_data_availability
from tools.report_formatter import format_report
from memory.workflow_state import Intent, WorkflowState

REQUIRED_FILES = [
    "salary_data.csv",
    "market_hiring_data.csv",
    "employee_attrition.csv",
    "workforce_headcount.csv",
]

INTENT_SYSTEM_PROMPT = """Extract the workforce query intent. Return ONLY a JSON object:
{
  "job_family": "<job family mentioned, e.g. 'Software Engineer'>",
  "region": "<region or country mentioned, e.g. 'Ireland'>",
  "question_type": "<'full' | 'compensation' | 'attrition'>"
}
Use 'compensation' for salary/pay questions, 'attrition' for turnover/retention questions,
and 'full' for questions that span multiple dimensions or are ambiguous."""


def _parse_intent(query: str) -> Intent:
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=INTENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )
    return Intent(**extract_json(response.content[0].text))


def run_streaming(query: str, on_event: callable) -> None:
    """Run the full agent pipeline, emitting real-time events via on_event(type, data)."""
    state = WorkflowState(query=query)

    availability = check_data_availability(REQUIRED_FILES)
    missing = [f for f, exists in availability.items() if not exists]
    if missing:
        state.errors.append(f"Missing data files: {missing}")

    on_event("plan", {"message": "Analysing query intent..."})
    try:
        state.intent = _parse_intent(query)
        on_event("plan", {
            "job_family": state.intent.job_family,
            "region": state.intent.region,
            "question_type": state.intent.question_type,
            "pipeline": [
                "Research Agent",
                "Workforce Analytics Agent",
                "Financial Impact Agent",
                "Strategy Agent",
                "Report Generator Agent",
            ],
        })
    except Exception as e:
        on_event("error", {"message": f"Intent parsing failed: {e}"})
        return

    # Research Agent
    on_event("agent_start", {"agent": "Research Agent"})
    if "salary_data.csv" not in missing:
        try:
            def _on_research(t, d):
                on_event("agent_thought", {"agent": "Research Agent", "thought_type": t, "data": d})
            state.research_output = run_research_agent(state.intent, on_event=_on_research)
            on_event("agent_done", {
                "agent": "Research Agent",
                "summary": (
                    f"Market median: €{state.research_output.market_median_salary:,.0f} · "
                    f"Company avg: €{state.research_output.company_avg_salary:,.0f} · "
                    f"Gap: {state.research_output.salary_gap_pct:.1f}% below market · "
                    f"Trend: {state.research_output.demand_trend} (+{state.research_output.yoy_growth_rate:.1f}% YoY)"
                ),
            })
        except Exception as e:
            state.errors.append(f"Research agent failed: {e}")
            on_event("agent_error", {"agent": "Research Agent", "message": str(e)})
    else:
        on_event("agent_skip", {"agent": "Research Agent", "reason": "salary_data.csv not found"})

    # Workforce Analytics Agent
    on_event("agent_start", {"agent": "Workforce Analytics Agent"})
    if "employee_attrition.csv" not in missing and "workforce_headcount.csv" not in missing:
        try:
            def _on_analytics(t, d):
                on_event("agent_thought", {"agent": "Workforce Analytics Agent", "thought_type": t, "data": d})
            state.analytics_output = run_workforce_analytics_agent(state.intent, on_event=_on_analytics)
            on_event("agent_done", {
                "agent": "Workforce Analytics Agent",
                "summary": (
                    f"Attrition: {state.analytics_output.attrition_rate:.1f}% ({state.analytics_output.risk_level} risk) · "
                    f"Headcount: {state.analytics_output.headcount} · "
                    f"Highest risk: {state.analytics_output.highest_risk_segment} · "
                    f"Avg tenure: {state.analytics_output.avg_tenure_years:.1f} yrs"
                ),
            })
        except Exception as e:
            state.errors.append(f"Workforce analytics agent failed: {e}")
            on_event("agent_error", {"agent": "Workforce Analytics Agent", "message": str(e)})
    else:
        on_event("agent_skip", {"agent": "Workforce Analytics Agent", "reason": "attrition/headcount data not found"})

    # Financial Impact Agent
    on_event("agent_start", {"agent": "Financial Impact Agent"})
    if state.research_output and state.analytics_output:
        try:
            def _on_financial(t, d):
                on_event("agent_thought", {"agent": "Financial Impact Agent", "thought_type": t, "data": d})
            state.financial_output = run_financial_impact_agent(
                state.research_output, state.analytics_output, on_event=_on_financial
            )
            rec = state.financial_output.recommended_scenario
            rec_scenario = next(
                (s for s in state.financial_output.scenarios if s.name == rec),
                state.financial_output.scenarios[0],
            )
            on_event("agent_done", {
                "agent": "Financial Impact Agent",
                "summary": (
                    f"Recommended: {rec_scenario.name} · "
                    f"Total cost: €{rec_scenario.total_cost_impact:,.0f} · "
                    f"Per head: €{rec_scenario.per_head_impact:,.0f}"
                ),
            })
        except Exception as e:
            state.errors.append(f"Financial impact agent failed: {e}")
            on_event("agent_error", {"agent": "Financial Impact Agent", "message": str(e)})
    else:
        on_event("agent_skip", {"agent": "Financial Impact Agent", "reason": "requires Research + Analytics outputs"})

    # Strategy Agent
    on_event("agent_start", {"agent": "Strategy Agent"})
    if state.research_output or state.analytics_output or state.financial_output:
        try:
            def _on_strategy(t, d):
                on_event("agent_thought", {"agent": "Strategy Agent", "thought_type": t, "data": d})
            state.strategy_output = run_strategy_agent(
                state.research_output, state.analytics_output, state.financial_output, on_event=_on_strategy
            )
            on_event("agent_done", {
                "agent": "Strategy Agent",
                "summary": state.strategy_output.recommendation[:150] + ("..." if len(state.strategy_output.recommendation) > 150 else ""),
            })
        except Exception as e:
            state.errors.append(f"Strategy agent failed: {e}")
            on_event("agent_error", {"agent": "Strategy Agent", "message": str(e)})

    # Report Generator Agent
    on_event("agent_start", {"agent": "Report Generator Agent"})
    try:
        def _on_report(t, d):
            on_event("agent_thought", {"agent": "Report Generator Agent", "thought_type": t, "data": d})
        report = run_report_generator_agent(state, on_event=_on_report)
        report_md = format_report(report.model_dump())
        on_event("agent_done", {"agent": "Report Generator Agent", "summary": "Executive report compiled successfully."})
        on_event("report", {"markdown": report_md})
    except Exception as e:
        state.errors.append(f"Report generator failed: {e}")
        on_event("agent_error", {"agent": "Report Generator Agent", "message": str(e)})

    if state.errors:
        on_event("warnings", {"warnings": state.errors})


def run(query: str) -> tuple[WorkflowState, str]:
    state = WorkflowState(query=query)

    # 1. Validate data availability
    availability = check_data_availability(REQUIRED_FILES)
    missing = [f for f, exists in availability.items() if not exists]
    if missing:
        state.errors.append(f"Missing data files: {missing}")

    # 2. Parse intent
    try:
        state.intent = _parse_intent(query)
    except Exception as e:
        state.errors.append(f"Intent parsing failed: {e}")
        return state, "Could not parse query intent."

    # 3. Research Agent — market benchmarking
    if "salary_data.csv" not in missing:
        try:
            state.research_output = run_research_agent(state.intent)
        except Exception as e:
            state.errors.append(f"Research agent failed: {e}")

    # 4. Workforce Analytics Agent — attrition and retention signals
    if "employee_attrition.csv" not in missing and "workforce_headcount.csv" not in missing:
        try:
            state.analytics_output = run_workforce_analytics_agent(state.intent)
        except Exception as e:
            state.errors.append(f"Workforce analytics agent failed: {e}")

    # 5. Financial Impact Agent — requires both research and analytics outputs
    if state.research_output and state.analytics_output:
        try:
            state.financial_output = run_financial_impact_agent(
                state.research_output, state.analytics_output
            )
        except Exception as e:
            state.errors.append(f"Financial impact agent failed: {e}")

    # 6. Strategy Agent — synthesises all available outputs into a recommendation
    if state.research_output or state.analytics_output or state.financial_output:
        try:
            state.strategy_output = run_strategy_agent(
                state.research_output, state.analytics_output, state.financial_output
            )
        except Exception as e:
            state.errors.append(f"Strategy agent failed: {e}")

    # 7. Report Generator Agent — produces the final executive report
    try:
        report = run_report_generator_agent(state)
        report_md = format_report(report.model_dump())
    except Exception as e:
        state.errors.append(f"Report generator failed: {e}")
        report_md = format_report({
            "market_benchmarking": str(state.research_output) if state.research_output else "_Unavailable._",
            "workforce_analytics": str(state.analytics_output) if state.analytics_output else "_Unavailable._",
            "financial_impact": str(state.financial_output) if state.financial_output else "_Unavailable._",
            "strategic_recommendation": str(state.strategy_output) if state.strategy_output else "_Unavailable._",
        })

    return state, report_md
