from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "software-verification" / "scripts" / "assess_metered_verification.py"
SKILL = ROOT / "skills" / "software-verification" / "SKILL.md"

SPEC = importlib.util.spec_from_file_location("assess_metered_verification", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
NOW = datetime(2026, 8, 12, 12, 10, tzinfo=timezone.utc)


def base_plan(**changes: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "format": "testforge-metered-verification/v1",
        "provider": "github-actions",
        "capacity_billing_scope": "user:Stunspot",
        "execution_billing_scope": "user:Stunspot",
        "observed_at": "2026-08-12T12:00:00Z",
        "valid_until": "2026-08-12T12:30:00Z",
        "evidence_source": "GitHub billing API",
        "refresh_at": "2026-09-01T00:00:00Z",
        "capacity_status": "observed",
        "remaining_minutes": 100,
        "reserve_minutes": 20,
        "paid_overage_available": False,
        "paid_overage_authorization": None,
        "planned_runs": [
            {"name": "pull_request", "jobs": [{"ceiling_minutes": 20}]}
        ],
    }
    plan.update(changes)
    return plan


class MeteredVerificationTests(unittest.TestCase):
    def test_exact_capacity_plus_reserve_proceeds(self) -> None:
        result = MODULE.assess(base_plan(remaining_minutes=40), now=NOW)
        self.assertEqual(result["outcome"], "PROCEED")
        self.assertTrue(result["automatic_invocation_permitted"])

    def test_unavailable_provider_holds_even_without_numeric_allowance(self) -> None:
        result = MODULE.assess(
            base_plan(capacity_status="unavailable", remaining_minutes=None), now=NOW
        )
        self.assertEqual(result["outcome"], "HOLD_PROVIDER_UNAVAILABLE")
        self.assertFalse(result["automatic_invocation_permitted"])

    def test_unknown_capacity_holds_instead_of_probing(self) -> None:
        result = MODULE.assess(
            base_plan(capacity_status="unknown", remaining_minutes=None), now=NOW
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
            ),
            now=NOW,
        )
        self.assertEqual(result["estimated_minutes"], 80)
        self.assertEqual(
            result["run_estimates"],
            [
                {"name": "push", "estimated_minutes": 40},
                {"name": "pull_request", "estimated_minutes": 40},
            ],
        )

    def test_billing_multiplier_is_counted(self) -> None:
        result = MODULE.assess(
            base_plan(
                reserve_minutes=0,
                planned_runs=[
                    {
                        "name": "weighted-runner",
                        "jobs": [
                            {"ceiling_minutes": 10, "billing_multiplier": 2.5}
                        ],
                    }
                ],
            ),
            now=NOW,
        )
        self.assertEqual(result["estimated_minutes"], 25)

    def test_reserve_is_not_silently_consumed(self) -> None:
        result = MODULE.assess(base_plan(remaining_minutes=20), now=NOW)
        self.assertEqual(result["outcome"], "HOLD_RESERVE")

    def test_paid_overage_requires_explicit_authority(self) -> None:
        pending = MODULE.assess(
            base_plan(remaining_minutes=0, paid_overage_available=True), now=NOW
        )
        approved = MODULE.assess(
            base_plan(
                remaining_minutes=0,
                paid_overage_available=True,
                paid_overage_authorization={
                    "authorization_id": "decision:123",
                    "authorized_by": "stunspot",
                    "authorized_at": "2026-08-12T12:05:00Z",
                    "valid_until": "2026-08-12T13:00:00Z",
                    "billing_scope": "user:Stunspot",
                    "max_paid_minutes": 20,
                },
            ),
            now=NOW,
        )
        self.assertEqual(pending["outcome"], "AUTHORITY_REQUIRED_PAID")
        self.assertFalse(pending["automatic_invocation_permitted"])
        self.assertEqual(approved["outcome"], "PROCEED_PAID_AUTHORIZED")
        self.assertTrue(approved["automatic_invocation_permitted"])

    def test_paid_authority_cannot_expand_beyond_its_bound(self) -> None:
        result = MODULE.assess(
            base_plan(
                remaining_minutes=0,
                paid_overage_available=True,
                planned_runs=[
                    {"name": "huge", "jobs": [{"ceiling_minutes": 1_000_000}]}
                ],
                paid_overage_authorization={
                    "authorization_id": "decision:tiny",
                    "authorized_by": "stunspot",
                    "authorized_at": "2026-08-12T12:05:00Z",
                    "valid_until": "2026-08-12T13:00:00Z",
                    "billing_scope": "user:Stunspot",
                    "max_paid_minutes": 20,
                },
            ),
            now=NOW,
        )
        self.assertEqual(result["outcome"], "AUTHORITY_REQUIRED_PAID")
        self.assertFalse(result["automatic_invocation_permitted"])

    def test_malformed_or_stale_snapshot_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.PlanError, "valid ISO 8601"):
            MODULE.assess(base_plan(observed_at="not-a-date"), now=NOW)
        with self.assertRaisesRegex(MODULE.PlanError, "expired"):
            MODULE.assess(
                base_plan(
                    observed_at="2026-08-12T10:00:00Z",
                    valid_until="2026-08-12T10:30:00Z",
                ),
                now=NOW,
            )

    def test_capacity_must_belong_to_execution_billing_scope(self) -> None:
        with self.assertRaisesRegex(MODULE.PlanError, "exactly match"):
            MODULE.assess(
                base_plan(execution_billing_scope="org:SomeoneElse"), now=NOW
            )

    def test_skill_makes_capacity_preflight_mandatory(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Preflight metered verification", text)
        self.assertIn("Do not launch a metered check merely to discover", text)
        self.assertIn("scripts/assess_metered_verification.py", text)


if __name__ == "__main__":
    unittest.main()
