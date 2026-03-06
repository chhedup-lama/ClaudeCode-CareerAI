from agents.base import client, MODEL, extract_json
from agents.research import run_research_agent
from tools.data_loader import check_data_availability
from tools.report_formatter import format_report
from memory.workflow_state import Intent, WorkflowState

REQUIRED_FILES = [
    "salary_data.csv",
    "market_hiring_data.csv",
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


def _partial_report(state: WorkflowState) -> str:
    """Produces a plain Markdown summary from whatever state fields are populated.
    Used as a fallback until the Report Generator Agent is built."""
    sections = {}

    if state.research_output:
        r = state.research_output
        gap_direction = "below" if r.salary_gap_pct > 0 else "above"
        sections["market_benchmarking"] = (
            f"Market median salary for {state.intent.job_family} in {state.intent.region}: "
            f"€{r.market_median_salary:,.0f}. "
            f"Company average salary: €{r.company_avg_salary:,.0f} "
            f"({abs(r.salary_gap_pct):.1f}% {gap_direction} market). "
            f"Market demand trend: {r.demand_trend} (YoY growth: {r.yoy_growth_rate:.1f}%)."
        )
    else:
        sections["market_benchmarking"] = "_Not yet available._"

    sections["workforce_analytics"] = "_Workforce Analytics Agent not yet built._"
    sections["financial_impact"] = "_Financial Impact Agent not yet built._"
    sections["strategic_recommendation"] = "_Strategy Agent not yet built._"

    return format_report(sections)


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

    # 3. Run Research Agent
    if "salary_data.csv" not in missing:
        try:
            state.research_output = run_research_agent(state.intent)
        except Exception as e:
            state.errors.append(f"Research agent failed: {e}")

    # 4. Produce partial report
    report_md = _partial_report(state)

    return state, report_md
