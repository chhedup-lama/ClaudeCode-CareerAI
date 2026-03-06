"""
Isolated test for the Research Agent.
Run: python test_research_agent.py
"""
from memory.workflow_state import Intent
from agents.research import run_research_agent

intent = Intent(
    job_family="Software Engineer",
    region="Ireland",
    question_type="compensation",
)

print(f"Running Research Agent for: {intent.job_family} in {intent.region}\n")
print("-" * 50)

output = run_research_agent(intent)

print(f"Market median salary : €{output.market_median_salary:,.0f}")
print(f"Company avg salary   : €{output.company_avg_salary:,.0f}")
print(f"Salary gap           : {output.salary_gap_pct:.1f}%")
print(f"YoY growth rate      : {output.yoy_growth_rate:.1f}%")
print(f"Demand trend         : {output.demand_trend}")
print(f"Source rows          : {output.source_rows}")
