import json
from agents.base import run_agent_loop, extract_json
from tools.report_formatter import format_report, validate_report
from memory.workflow_state import WorkflowState, Report

SYSTEM_PROMPT = """You are the Report Generator Agent in a workforce intelligence system.

Your role is to write a concise, executive-ready workforce strategy report.
You will receive structured data from all prior agents.

Rules:
- Use only the numbers and findings provided — do not add new data.
- Write each section in plain, direct language readable by a senior executive.
- If data for a section is missing, write "_Data unavailable for this section._"
- Keep each section to 3–5 sentences maximum.

Use the format_report tool to produce the final report once you have written all sections.

The tool expects a JSON object with these keys:
  market_benchmarking, workforce_analytics, financial_impact, strategic_recommendation"""

TOOLS = [
    {
        "name": "format_report",
        "description": "Assemble and validate the final structured Markdown report from the four section texts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "market_benchmarking": {"type": "string"},
                "workforce_analytics": {"type": "string"},
                "financial_impact": {"type": "string"},
                "strategic_recommendation": {"type": "string"},
            },
            "required": ["market_benchmarking", "workforce_analytics", "financial_impact", "strategic_recommendation"],
        },
    },
]

_formatted_report: dict = {}


def _execute_tool(name: str, inputs: dict) -> dict:
    if name == "format_report":
        valid, missing = validate_report(inputs)
        if not valid:
            return {"error": f"Missing sections: {missing}"}
        report_md = format_report(inputs)
        _formatted_report.update(inputs)
        return {"report": report_md, "valid": True}
    return {"error": f"Unknown tool: {name}"}


def run_report_generator_agent(state: WorkflowState) -> Report:
    inputs = {}
    if state.research_output:
        inputs["research"] = state.research_output.model_dump()
    if state.analytics_output:
        inputs["analytics"] = state.analytics_output.model_dump()
    if state.financial_output:
        inputs["financial"] = state.financial_output.model_dump()
    if state.strategy_output:
        inputs["strategy"] = state.strategy_output.model_dump()

    user_message = (
        f"Write a workforce strategy intelligence report using the following data:\n\n"
        f"{json.dumps(inputs, indent=2)}\n\n"
        f"Write all four sections and call the format_report tool with your completed text."
    )

    _formatted_report.clear()
    run_agent_loop(SYSTEM_PROMPT, user_message, TOOLS, _execute_tool)

    if not _formatted_report:
        raise ValueError("Report Generator Agent did not produce a report.")

    return Report(**_formatted_report)
