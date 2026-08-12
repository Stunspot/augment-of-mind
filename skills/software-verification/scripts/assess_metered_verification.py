#!/usr/bin/env python3
"""Evaluate a recorded quota snapshot and complete metered test plan."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


FORMAT = "testforge-metered-verification/v1"
PROCEED_OUTCOMES = {"PROCEED", "PROCEED_PAID_AUTHORIZED"}


class PlanError(ValueError):
    """Raised when a capacity snapshot or run plan is malformed."""


def decimal_field(value: Any, field: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise PlanError(f"{field} must be a number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise PlanError(f"{field} must be a number") from error
    if not number.is_finite() or number < 0 or (positive and number == 0):
        qualifier = "positive" if positive else "non-negative"
        raise PlanError(f"{field} must be a finite {qualifier} number")
    return number


def integer_field(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PlanError(f"{field} must be a positive integer")
    return value


def json_number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def assess(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("format") != FORMAT:
        raise PlanError(f"format must be {FORMAT}")
    provider = plan.get("provider")
    observed_at = plan.get("observed_at")
    evidence_source = plan.get("evidence_source")
    if not isinstance(provider, str) or not provider.strip():
        raise PlanError("provider must be a non-empty string")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise PlanError("observed_at must be a non-empty string")
    if not isinstance(evidence_source, str) or not evidence_source.strip():
        raise PlanError("evidence_source must be a non-empty string")

    capacity_status = plan.get("capacity_status")
    if capacity_status not in {"observed", "unavailable", "unknown"}:
        raise PlanError("capacity_status must be observed, unavailable, or unknown")

    reserve = decimal_field(plan.get("reserve_minutes", 0), "reserve_minutes")
    remaining_value = plan.get("remaining_minutes")
    if capacity_status == "observed" and remaining_value is None:
        raise PlanError("remaining_minutes is required when capacity_status is observed")
    remaining = None if remaining_value is None else decimal_field(remaining_value, "remaining_minutes")

    paid_available = plan.get("paid_overage_available")
    paid_authorized = plan.get("paid_overage_authorized", False)
    if paid_available is not True and paid_available is not False and paid_available is not None:
        raise PlanError("paid_overage_available must be true, false, or null")
    if not isinstance(paid_authorized, bool):
        raise PlanError("paid_overage_authorized must be a boolean")
    if paid_authorized and paid_available is not True:
        raise PlanError("paid overage cannot be authorized unless it is available")

    planned_runs = plan.get("planned_runs")
    if not isinstance(planned_runs, list) or not planned_runs:
        raise PlanError("planned_runs must be a non-empty list")

    total = Decimal(0)
    run_estimates: list[dict[str, Any]] = []
    for run_index, run in enumerate(planned_runs):
        if not isinstance(run, dict):
            raise PlanError(f"planned_runs[{run_index}] must be an object")
        name = run.get("name")
        jobs = run.get("jobs")
        if not isinstance(name, str) or not name.strip():
            raise PlanError(f"planned_runs[{run_index}].name must be a non-empty string")
        if not isinstance(jobs, list) or not jobs:
            raise PlanError(f"planned_runs[{run_index}].jobs must be a non-empty list")
        run_total = Decimal(0)
        for job_index, job in enumerate(jobs):
            if not isinstance(job, dict):
                raise PlanError(f"{name}.jobs[{job_index}] must be an object")
            prefix = f"{name}.jobs[{job_index}]"
            ceiling = decimal_field(job.get("ceiling_minutes"), f"{prefix}.ceiling_minutes", positive=True)
            count = integer_field(job.get("count", 1), f"{prefix}.count")
            attempts = integer_field(job.get("attempts", 1), f"{prefix}.attempts")
            multiplier = decimal_field(job.get("billing_multiplier", 1), f"{prefix}.billing_multiplier", positive=True)
            run_total += ceiling * count * attempts * multiplier
        total += run_total
        run_estimates.append({"name": name, "estimated_minutes": json_number(run_total)})

    required_with_reserve = total + reserve
    if capacity_status == "unavailable":
        outcome = "HOLD_PROVIDER_UNAVAILABLE"
    elif capacity_status == "unknown" or remaining is None:
        outcome = "HOLD_UNKNOWN"
    elif remaining >= required_with_reserve:
        outcome = "PROCEED"
    elif paid_available is True and paid_authorized:
        outcome = "PROCEED_PAID_AUTHORIZED"
    elif paid_available is True:
        outcome = "AUTHORITY_REQUIRED_PAID"
    elif remaining >= total:
        outcome = "HOLD_RESERVE"
    else:
        outcome = "HOLD_INSUFFICIENT"

    return {
        "format": FORMAT,
        "provider": provider,
        "observed_at": observed_at,
        "evidence_source": evidence_source,
        "refresh_at": plan.get("refresh_at"),
        "capacity_status": capacity_status,
        "remaining_minutes": None if remaining is None else json_number(remaining),
        "reserve_minutes": json_number(reserve),
        "estimated_minutes": json_number(total),
        "required_with_reserve_minutes": json_number(required_with_reserve),
        "run_estimates": run_estimates,
        "paid_overage_available": paid_available,
        "paid_overage_authorized": paid_authorized,
        "outcome": outcome,
        "automatic_invocation_permitted": outcome in PROCEED_OUTCOMES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="JSON capacity snapshot and expanded run plan")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise PlanError("plan root must be an object")
        result = assess(data)
    except (OSError, json.JSONDecodeError, PlanError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["automatic_invocation_permitted"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
