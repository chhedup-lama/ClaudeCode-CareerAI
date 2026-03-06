REQUIRED_SECTIONS = [
    "market_benchmarking",
    "workforce_analytics",
    "financial_impact",
    "strategic_recommendation",
]

SECTION_TITLES = {
    "market_benchmarking": "## 1. Market Benchmarking",
    "workforce_analytics": "## 2. Workforce Analytics",
    "financial_impact": "## 3. Financial Impact",
    "strategic_recommendation": "## 4. Strategic Recommendation",
}


def format_report(sections: dict) -> str:
    lines = ["# Workforce Strategy Intelligence Report\n"]
    for key, title in SECTION_TITLES.items():
        lines.append(title)
        lines.append(sections.get(key, "_Data unavailable for this section._"))
        lines.append("")
    return "\n".join(lines)


def validate_report(sections: dict) -> tuple[bool, list[str]]:
    missing = [s for s in REQUIRED_SECTIONS if not sections.get(s)]
    return len(missing) == 0, missing
