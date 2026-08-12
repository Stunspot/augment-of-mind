from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "software-verification" / "scripts" / "assess_metered_verification.py"
SKILL = ROOT / "skills" / "software-verification" / "SKILL.md"

SPEC = importlib.util.spec_from_file_location("assess_metered_verification", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def base_plan(**changes: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "format": "testforge-metered-verification/v1",
        "provider": "github-actions",
        "observed_at": "2026-08-12T12:00:00Z",
        "evidence_source": "GitHub billing API",
        "refresh_at": "2026-09-01T00:00:00Z",
        "capacity_status": "observed",
        "remaining_minutes": 100,
        "reserve_minutes": 20,
        "paid_overage_available": False,
        "paid_overage_authorized": False,
        "planned_runs": [
            {"name": "pull_request", "jobs": [{"ceiling_minutes": 20}]}
        ],
    }
    plan.update(changes)
    return plan


class MeteredVerificationTests(unittest.TestCase):
    def test_exact_capacity_plus_reserve_proceeds(self) -> None:
        result = MODULE.assess(base_plan(remaining_minutes=40))
        self.assertEqual(result["outcome"], "PROCEED")
        self.assertTrue(result["automatic_invocation_permitted"])

    def test_unavailable_provider_holds_even_without_numeric_allowance(self) -> None:
        result = MODULE.assess(
            base_plan(capacity_status="unavailable", remaining_minutes=None)
        )
        self.assertEqual(result["outcome"], "HOLD_PROVIDER_UNAVAILABLE")
        self.assertFalse(result["automatic_invocation_permitted"])

    def test_unknown_capacity_holds_instead_of_probing(self) -> None:
        result = MODULE.assess(
            base_plan(capacity_status="unknown", remaining_minutes=None)
        )
        self.assertEqual(result["outcome"], "HOLD_UNKNOWN")
        self.assertFalse(result["automatic_invocation_permitted"])

    def test_duplicate_triggers_matrix_and_attempts_are_all_counted(self) -> None:
        jobs = [{"ceiling_minutes": 10, "count": 2, "attempts": 2}]
        result = MODULE.assess(
            base_plan(
                remaining_minutes=100,
                reserve_minutes=0,
                planned_runs=[
                    {"name": "push", "jobs": jobs},
                    {"name": "pull_request", "jobs": jobs},
                ],
            )
        )
        self.assertEqual(result["estimated_minutes"], 80)
        self.assertEqual(
            result["run_estimates"],
            [
                {"name": "push", "estimated_minutes": 40},
                {"name": "pull_request", "estimated_minutes": 40},
            ],
        )

    def test_reserve_is_not_silently_consumed(self) -> None:
        result = MODULE.assess(base_plan(remaining_minutes=20))
        self.assertEqual(result["outcome"], "HOLD_RESERVE")

    def test_paid_overage_requires_explicit_authority(self) -> None:
        pending = MODULE.assess(
            base_plan(remaining_minutes=0, paid_overage_available=True)
        )
        approved = MODULE.assess(
            base_plan(
                remaining_minutes=0,
                paid_overage_available=True,
                paid_overage_authorized=True,
            )
        )
        self.assertEqual(pending["outcome"], "AUTHORITY_REQUIRED_PAID")
        self.assertFalse(pending["automatic_invocation_permitted"])
        self.assertEqual(approved["outcome"], "PROCEED_PAID_AUTHORIZED")
        self.assertTrue(approved["automatic_invocation_permitted"])

    def test_skill_makes_capacity_preflight_mandatory(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Preflight metered verification", text)
        self.assertIn("Do not launch a metered check merely to discover", text)
        self.assertIn("scripts/assess_metered_verification.py", text)


if __name__ == "__main__":
    unittest.main()
