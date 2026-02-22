from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import json


class OutputWriter:
    def __init__(self, output_dir: str = "outputs") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def write_json(self, prefix: str, payload: Dict[str, Any]) -> str:
        path = self.output_dir / f"{prefix}_{self._timestamp()}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def write_talking_points(self, mode: str, consensus: Dict[str, Any]) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        strengths = consensus.get("top_strengths", [])
        gaps = consensus.get("top_gaps", [])
        investor_narrative = consensus.get("investor_narrative_60s", "")
        interview_narrative = consensus.get("interview_narrative_60s", "")
        past_work = consensus.get("past_work_leverage", [])
        next_steps = consensus.get("highest_roi_next_steps_30d", [])
        customer_changes = consensus.get("customer_requested_changes", [])
        website_changes = consensus.get("website_change_recommendations", [])
        investor_questions = consensus.get("realistic_investor_questions", [])
        investor_answers = consensus.get("suggested_strong_answers", [])
        follow_ups = consensus.get("likely_follow_up_questions", [])
        red_flags = consensus.get("diligence_red_flags", [])
        funding_use_plan = consensus.get("funding_use_plan", [])

        lines = [
            "CHARTROOM TALKING POINTS",
            f"Mode: {mode}",
            f"Date: {ts}",
            "",
            "Top 5 Strengths:",
        ]
        for idx, s in enumerate(strengths[:5], start=1):
            lines.append(f"{idx}. {s}")

        lines.append("")
        lines.append("Top 5 Gaps to Fix:")
        for idx, g in enumerate(gaps[:5], start=1):
            lines.append(f"{idx}. {g}")

        lines.extend([
            "",
            "Investor Narrative (60 sec):",
            investor_narrative,
            "",
            "Interview Narrative (60 sec):",
            interview_narrative,
            "",
            "Past Work Leverage for Future Interviews:",
        ])
        for item in past_work:
            lines.append(f"- {item}")

        lines.extend(["", "Highest ROI Next Steps (30 days):"])
        for idx, step in enumerate(next_steps, start=1):
            lines.append(f"{idx}. {step}")

        if customer_changes:
            lines.extend(["", "Customer-Requested Changes:"])
            for idx, change in enumerate(customer_changes, start=1):
                lines.append(f"{idx}. {change}")

        if website_changes:
            lines.extend(["", "Website Changes to Improve Customer Adoption:"])
            for idx, change in enumerate(website_changes, start=1):
                lines.append(f"{idx}. {change}")

        if investor_questions:
            lines.extend(["", "Realistic Investor Questions:"])
            for idx, question in enumerate(investor_questions, start=1):
                lines.append(f"{idx}. {question}")

        if investor_answers:
            lines.extend(["", "Suggested Strong Answers:"])
            for idx, answer in enumerate(investor_answers, start=1):
                lines.append(f"{idx}. {answer}")

        if follow_ups:
            lines.extend(["", "Likely Follow-up Questions:"])
            for idx, question in enumerate(follow_ups, start=1):
                lines.append(f"{idx}. {question}")

        if red_flags:
            lines.extend(["", "Diligence Red Flags to Prepare For:"])
            for idx, item in enumerate(red_flags, start=1):
                lines.append(f"{idx}. {item}")

        if funding_use_plan:
            lines.extend(["", "Funding Use Plan:"])
            for idx, item in enumerate(funding_use_plan, start=1):
                lines.append(f"{idx}. {item}")

        out = "\n".join(lines)
        path = self.output_dir / f"talking_points_{self._timestamp()}.txt"
        path.write_text(out, encoding="utf-8")
        return str(path)
