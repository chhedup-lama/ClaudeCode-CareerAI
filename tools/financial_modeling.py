def model_salary_increase(headcount: int, avg_salary: float, pct_increase: float) -> dict:
    per_head = round(avg_salary * (pct_increase / 100), 2)
    total = round(per_head * headcount, 2)
    return {
        "name": f"{pct_increase}% salary increase",
        "pct_increase": pct_increase,
        "per_head_impact": per_head,
        "total_cost_impact": total,
    }


def model_hiring_cost(headcount: int, cost_per_hire: float) -> dict:
    return {
        "headcount": headcount,
        "cost_per_hire": cost_per_hire,
        "total_cost": round(headcount * cost_per_hire, 2),
    }


def compare_scenarios(scenarios: list[dict]) -> list[dict]:
    return sorted(scenarios, key=lambda s: s.get("total_cost_impact", 0))
