import json
from agents.base import run_agent_loop, extract_json
from memory.workflow_state import ResearchOutput, AnalyticsOutput, FinancialOutput, StrategyOutput

SYSTEM_PROMPT = """You are the Strategy Agent in a workforce intelligence system.

Your role is to synthesize insights from research, workforce analytics, and financial modeling
into a clear, evidence-based workforce recommendation.

Rules:
- Only use numbers and findings already present in the inputs.
- Do not invent data points.
- Evaluate trade-offs explicitly.
- Quantify the risk of inaction where possible.

Respond with ONLY a JSON object:
{
  "recommendation": <string, clear action statement>,
  "rationale": <string, explanation referencing the input data>,
  "risk_if_unchanged": <string, consequence of taking no action>
}"""


def run_strategy_agent(
    research: ResearchOutput | None,
    analytics: AnalyticsOutput | None,
    financial: FinancialOutput | None,
    on_event: callable | None = None,
) -> StrategyOutput:
    inputs = {}
    if research:
        inputs["market_research"] = research.model_dump()
    if analytics:
        inputs["workforce_analytics"] = analytics.model_dump()
    if financial:
        inputs["financial_modeling"] = financial.model_dump()

    user_message = (
        f"Synthesize the following workforce intelligence data into a strategic recommendation:\n\n"
        f"{json.dumps(inputs, indent=2)}\n\n"
        f"Return your recommendation as a JSON object."
    )
    if on_event:
        on_event("thinking", {"message": "Synthesising research, analytics, and financial data into a strategic recommendation..."})
    result = run_agent_loop(SYSTEM_PROMPT, user_message, tools=None, tool_executor=None, on_event=on_event)
    return StrategyOutput(**extract_json(result))
