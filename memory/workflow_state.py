from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Intent(BaseModel):
    job_family: str
    region: str
    question_type: str  # "full" | "compensation" | "attrition"


class ResearchOutput(BaseModel):
    market_median_salary: float
    company_avg_salary: float
    salary_gap_pct: float
    yoy_growth_rate: float
    demand_trend: Optional[str] = "stable"  # "increasing" | "stable" | "decreasing"
    source_rows: int


class AnalyticsOutput(BaseModel):
    attrition_rate: float
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"
    highest_risk_segment: str
    headcount: int
    avg_tenure_years: float


class Scenario(BaseModel):
    name: str
    pct_increase: float
    total_cost_impact: float
    per_head_impact: float


class FinancialOutput(BaseModel):
    scenarios: list[Scenario]
    recommended_scenario: str


class StrategyOutput(BaseModel):
    recommendation: str
    rationale: str
    risk_if_unchanged: str


class Report(BaseModel):
    market_benchmarking: str
    workforce_analytics: str
    financial_impact: str
    strategic_recommendation: str


class WorkflowState(BaseModel):
    query: str
    intent: Optional[Intent] = None
    research_output: Optional[ResearchOutput] = None
    analytics_output: Optional[AnalyticsOutput] = None
    financial_output: Optional[FinancialOutput] = None
    strategy_output: Optional[StrategyOutput] = None
    report: Optional[Report] = None
    errors: list[str] = []
