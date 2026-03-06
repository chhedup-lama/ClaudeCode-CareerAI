import json
from agents.base import run_agent_loop, extract_json
from tools.financial_modeling import model_salary_increase, compare_scenarios
from memory.workflow_state import ResearchOutput, AnalyticsOutput, FinancialOutput, Scenario

SYSTEM_PROMPT = """You are the Financial Impact Agent in a workforce intelligence system.

Your role is to model the financial cost of workforce decisions using pre-analyzed data.
You will receive structured research and analytics outputs — do not access raw datasets.
Use your tools to model salary increase scenarios and compare them.

When complete, respond with ONLY a JSON object:
{
  "scenarios": [
    {"name": <str>, "pct_increase": <float>, "total_cost_impact": <float>, "per_head_impact": <float>},
    ...
  ],
  "recommended_scenario": <string, name of the most balanced scenario>
}"""

TOOLS = [
    {
        "name": "model_scenarios",
        "description": "Model the financial impact of salary increase scenarios given headcount and average salary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "headcount": {"type": "integer"},
                "avg_salary": {"type": "number"},
                "pct_increases": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of percentage increases to model, e.g. [5, 7, 10]",
                },
            },
            "required": ["headcount", "avg_salary", "pct_increases"],
        },
    },
]


def _execute_tool(name: str, inputs: dict) -> dict:
    if name == "model_scenarios":
        scenarios = [
            model_salary_increase(inputs["headcount"], inputs["avg_salary"], pct)
            for pct in inputs["pct_increases"]
        ]
        return {"scenarios": compare_scenarios(scenarios)}
    return {"error": f"Unknown tool: {name}"}


def run_financial_impact_agent(
    research: ResearchOutput,
    analytics: AnalyticsOutput,
    on_event: callable | None = None,
) -> FinancialOutput:
    context = json.dumps({
        "market_median_salary": research.market_median_salary,
        "company_avg_salary": research.company_avg_salary,
        "salary_gap_pct": research.salary_gap_pct,
        "headcount": analytics.headcount,
        "attrition_rate": analytics.attrition_rate,
        "risk_level": analytics.risk_level,
    }, indent=2)

    user_message = (
        f"Using the following workforce data, model the financial impact of salary adjustments:\n\n"
        f"{context}\n\n"
        f"Use your tool to model scenarios at 5%, 7%, and 10% salary increases. "
        f"Then recommend the most balanced scenario given the salary gap and attrition risk. "
        f"Return your findings as a JSON object."
    )
    result = run_agent_loop(SYSTEM_PROMPT, user_message, TOOLS, _execute_tool, on_event=on_event)
    data = extract_json(result)
    scenarios = [Scenario(**s) for s in data["scenarios"]]
    return FinancialOutput(scenarios=scenarios, recommended_scenario=data["recommended_scenario"])
