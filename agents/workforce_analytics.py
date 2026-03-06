from agents.base import run_agent_loop, extract_json
from tools.data_loader import load_csv, filter_dataset
from tools.attrition import compute_attrition_rate, segment_workforce, flag_risk, DEFAULT_RISK_THRESHOLD
from memory.workflow_state import Intent, AnalyticsOutput

SYSTEM_PROMPT = """You are the Workforce Analytics Agent in a workforce intelligence system.

Your role is to analyze internal workforce data: attrition risk, tenure patterns, and retention signals.
Use your tools to load and compute metrics from the employee datasets.
Never estimate attrition rates — only report what the data shows.

When you have gathered all required information, respond with ONLY a JSON object:
{
  "attrition_rate": <float, percentage>,
  "risk_level": <"LOW" | "MEDIUM" | "HIGH">,
  "highest_risk_segment": <string describing the group with highest attrition>,
  "headcount": <int>,
  "avg_tenure_years": <float>
}"""

TOOLS = [
    {
        "name": "get_attrition_rate",
        "description": "Compute the attrition rate for a job family and region from employee_attrition.csv.",
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
        "name": "get_highest_risk_segment",
        "description": "Identify the workforce segment with the highest attrition rate, broken down by level.",
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
        "name": "get_headcount_and_tenure",
        "description": "Get the headcount and average tenure for a job family and region from workforce_headcount.csv.",
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
    filters = {"job_family": inputs["job_family"], "region": inputs["region"]}

    if name == "get_attrition_rate":
        df = load_csv("employee_attrition.csv")
        filtered = filter_dataset(df, filters)
        if filtered.empty:
            return {"error": "No attrition data found for the given filters"}
        rate = compute_attrition_rate(filtered)
        risk = flag_risk(rate, DEFAULT_RISK_THRESHOLD)
        return {"attrition_rate": rate, "risk_level": risk, "rows_analyzed": len(filtered)}

    if name == "get_highest_risk_segment":
        df = load_csv("employee_attrition.csv")
        filtered = filter_dataset(df, filters)
        if filtered.empty:
            return {"error": "No attrition data found for the given filters"}
        segmented = segment_workforce(filtered, ["level"])
        if segmented.empty:
            return {"error": "Could not segment workforce by level"}
        worst = segmented.sort_values("attrition", ascending=False).iloc[0]
        level = worst.get("level", "unknown")
        rate = round(float(worst["attrition"]) * 100, 2)
        return {"highest_risk_segment": f"{level} ({rate}% attrition)"}

    if name == "get_headcount_and_tenure":
        df = load_csv("workforce_headcount.csv")
        filtered = filter_dataset(df, filters)
        if filtered.empty:
            return {"error": "No headcount data found for the given filters"}
        headcount = int(filtered["headcount"].sum())
        avg_tenure = round(float(filtered["avg_tenure_years"].mean()), 2) if "avg_tenure_years" in filtered.columns else 0.0
        return {"headcount": headcount, "avg_tenure_years": avg_tenure}

    return {"error": f"Unknown tool: {name}"}


def run_workforce_analytics_agent(intent: Intent) -> AnalyticsOutput:
    user_message = (
        f"Analyze the internal workforce for {intent.job_family} in {intent.region}. "
        f"Use your tools to compute: the overall attrition rate, risk level, "
        f"highest-risk workforce segment, headcount, and average tenure. "
        f"Return your findings as a JSON object."
    )
    result = run_agent_loop(SYSTEM_PROMPT, user_message, TOOLS, _execute_tool)
    return AnalyticsOutput(**extract_json(result))
