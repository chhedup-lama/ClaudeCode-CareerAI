# CareerAI — Workforce Intelligence System

A multi-agent AI system that supports HR and workforce strategy decisions by coordinating specialist agents to produce structured executive reports.

---

## What It Does

Given a natural language question like:

> *"Should we increase compensation for software engineers in Ireland next year?"*

The system runs a pipeline of AI agents across your HR datasets and returns a full **Workforce Strategy Intelligence Report** covering market benchmarking, attrition risk, financial impact, and a strategic recommendation.

---

## Architecture

```
User Query
    ↓
Orchestrator
    ↓
┌─────────────────────────────────────┐
│  Research Agent                     │  salary_data.csv + market_hiring_data.csv
│  Workforce Analytics Agent          │  employee_attrition.csv + workforce_headcount.csv
│  Financial Impact Agent             │  (uses Research + Analytics outputs)
│  Strategy Agent                     │  (synthesises all outputs)
│  Report Generator Agent             │  (produces executive Markdown report)
└─────────────────────────────────────┘
    ↓
Workforce Strategy Intelligence Report
```

---

## Agents

| Agent | Role |
|---|---|
| **Research** | Benchmarks market salaries, identifies compensation gaps, detects demand trends |
| **Workforce Analytics** | Computes attrition rate, risk level, highest-risk segment, headcount, tenure |
| **Financial Impact** | Models cost of salary increase scenarios (5%, 7%, 10%) and recommends the most balanced |
| **Strategy** | Synthesises all agent outputs into a trade-off-aware recommendation |
| **Report Generator** | Writes a concise, executive-ready Markdown report from structured agent data |

---

## Design Philosophy

- **LLMs reason, tools calculate** — deterministic tasks (medians, percentiles, YoY growth) are handled by Python tools, not the LLM
- **No hallucination** — every number in the report is grounded in a dataset row
- **Modular agents** — each agent owns a single cognitive responsibility
- **Graceful degradation** — the orchestrator skips agents if their required data is missing

---

## Data Sources

Simulated enterprise HR datasets in `data/`:

| File | Contents |
|---|---|
| `salary_data.csv` | Market salary benchmarks by job family, region, level, year |
| `market_hiring_data.csv` | External open roles and hiring demand by year |
| `employee_attrition.csv` | Internal attrition records by level and segment |
| `workforce_headcount.csv` | Internal headcount, average salary, and tenure |

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Running

```bash
python main.py "Should we increase compensation for software engineers in Ireland next year?"
```

### Example Output

```
# Workforce Strategy Intelligence Report

## 1. Market Benchmarking
Company average salary of €114,250 sits 1.93% below the market median of €116,500.
Market salaries growing at 9.04% YoY with increasing demand.

## 2. Workforce Analytics
Overall attrition rate: 38.89% (HIGH risk). Junior segment at 75% attrition.
Headcount: 91. Average tenure: 5.47 years.

## 3. Financial Impact
5% increase: €519k | 7% increase: €727k | 10% increase: €1.04M
Recommended: 7% salary increase.

## 4. Strategic Recommendation
Implement a targeted 7% salary increase, front-loaded to the Junior segment
to address the 75% attrition rate and close the growing market compensation gap.
```

---

## Project Structure

```
agents/
  base.py                 # Base agent loop with tool-use support
  orchestrator.py         # Coordinates the full agent pipeline
  research.py             # Market benchmarking agent
  workforce_analytics.py  # Attrition and retention agent
  financial_impact.py     # Financial modelling agent
  strategy.py             # Strategic synthesis agent
  report_generator.py     # Executive report writer agent

tools/
  data_loader.py          # CSV loading and filtering
  benchmarking.py         # Salary percentile and trend detection
  attrition.py            # Attrition rate computation and risk flagging
  financial_modeling.py   # Salary increase scenario modelling
  report_formatter.py     # Markdown report assembly and validation

memory/
  workflow_state.py       # Pydantic models for all agent inputs/outputs

data/                     # Simulated HR datasets
main.py                   # CLI entry point
```
