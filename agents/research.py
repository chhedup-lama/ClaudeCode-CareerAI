from agents.base import run_agent_loop, extract_json
from tools.data_loader import load_csv, filter_dataset
from tools.benchmarking import compute_benchmark, detect_trend
from memory.workflow_state import Intent, ResearchOutput

SYSTEM_PROMPT = """You are the Research Agent in a workforce intelligence system.

Your role is to analyze salary benchmark data and labor market demand data.
Use your tools to load, filter, and compute metrics from the datasets.
Ground every number in data returned by your tools — never estimate or invent figures.

When you have gathered all required information, respond with ONLY a JSON object:
{
  "market_median_salary": <float>,
  "company_avg_salary": <float>,
  "salary_gap_pct": <float, positive means company pays below market>,
  "yoy_growth_rate": <float, year-over-year market salary growth %>,
  "demand_trend": <"increasing" | "stable" | "decreasing">,
  "source_rows": <int, total data rows analyzed>
}"""

TOOLS = [
    {
        "name": "get_market_salary_benchmark",
        "description": "Compute the market salary benchmark for a job family and region from salary_data.csv.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_family": {"type": "string"},
                "region": {"type": "string"},
                "percentile": {"type": "number", "description": "50 for median, 75 for P75. Defaults to 50."},
            },
            "required": ["job_family", "region"],
        },
    },
    {
        "name": "get_company_avg_salary",
        "description": "Compute the internal company average salary for a job family and region from workforce_headcount.csv.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_family": {"type": "string"},
                "region": {"type": "string"},
            },
            "required": ["job_family", "region"],
        },
    },
    {
        "name": "get_market_demand_trend",
        "description": "Compute the year-over-year demand trend for a job family and region from market_hiring_data.csv.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_family": {"type": "string"},
                "region": {"type": "string"},
            },
            "required": ["job_family", "region"],
        },
    },
]


def _execute_tool(name: str, inputs: dict) -> dict:
    if name == "get_market_salary_benchmark":
        df = load_csv("salary_data.csv")
        filtered = filter_dataset(df, {"job_family": inputs["job_family"], "region": inputs["region"]})
        if filtered.empty:
            return {"error": "No market salary data found for the given filters"}
        benchmark = compute_benchmark(filtered, "salary", inputs.get("percentile", 50))
        return {"market_salary_benchmark": benchmark, "rows_analyzed": len(filtered)}

    if name == "get_company_avg_salary":
        df = load_csv("workforce_headcount.csv")
        filtered = filter_dataset(df, {"job_family": inputs["job_family"], "region": inputs["region"]})
        if filtered.empty:
            return {"error": "No internal headcount data found for the given filters"}
        avg = round(float(filtered["avg_salary"].mean()), 2)
        return {"company_avg_salary": avg, "rows_analyzed": len(filtered)}

    if name == "get_market_demand_trend":
        df = load_csv("market_hiring_data.csv")
        filtered = filter_dataset(df, {"job_family": inputs["job_family"], "region": inputs["region"]})
        if filtered.empty:
            return {"error": "No market hiring data found for the given filters"}
        trend = detect_trend(filtered, "open_roles")
        return {**trend, "rows_analyzed": len(filtered)}

    return {"error": f"Unknown tool: {name}"}


def run_research_agent(intent: Intent) -> ResearchOutput:
    user_message = (
        f"Analyze the labor market for {intent.job_family} in {intent.region}. "
        f"Use your tools to find the market median salary, the company average salary, "
        f"the salary gap percentage, and the year-over-year demand trend. "
        f"Return your findings as a JSON object."
    )
    result = run_agent_loop(SYSTEM_PROMPT, user_message, TOOLS, _execute_tool)
    return ResearchOutput(**extract_json(result))
