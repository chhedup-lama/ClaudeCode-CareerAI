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
