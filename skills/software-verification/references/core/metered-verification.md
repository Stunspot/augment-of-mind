# Metered verification preflight

Use this doctrine before hosted CI, device or browser farms, paid cloud tests, and any verification route constrained by an allowance, credit balance, spending limit, or finite reservation.

## Capacity record

Capture a fresh, attributable snapshot before proposing execution:

- provider and account or organization boundary;
- observation time, evidence source, and a validity deadline no more than 60 minutes later;
- the billing scope named by the snapshot and the billing scope the planned execution will consume; they must match exactly;
- `capacity_status`: `observed`, `unavailable`, or `unknown`;
- remaining included allowance when the provider exposes it;
- allowance refresh or billing-cycle boundary;
- whether paid overage exists and whether the principal explicitly authorized it;
- a principal-set reserve that this run must not consume.

An inaccessible allowance is `unknown`, not zero. A malformed, future-dated, expired, over-age, or pre-refresh snapshot observed before a billing-cycle rollover cannot authorize execution after that rollover. A provider refusal before any test step establishes `unavailable` for that attempted route; it is provider non-execution, not a product failure. Never run a job merely to discover whether the meter permits it.

## Complete run estimate

Count the entire execution graph, not one visible workflow label:

`estimated usage = sum(trigger copies x matrix jobs x attempts x job ceiling x billing multiplier)`

Include duplicate triggers such as `push` and `pull_request`, matrix expansion, reusable-workflow fan-out, retries or reruns, and the provider's current billing rule. Obtain provider-specific multipliers from current provider documentation or account data; do not preserve an old multiplier as lore.

Represent each expanded job in the input to `scripts/assess_metered_verification.py`, or use its `count` and `billing_multiplier` fields. A ceiling is deliberately conservative: optimization happens before launch, not after the allowance has gone to Valhalla.

## Decision

- `PROCEED`: observed included capacity covers the estimate and reserve.
- `PAID_DISPATCH_AUTHORIZED`: included capacity is insufficient, and an unexpired, unused principal authorization is bound to this exact execution ID, plan digest, billing scope, and maximum paid minutes. A separate dispatcher may proceed only after atomically consuming that authorization in durable custody.
- `HOLD_RESERVE`: the run fits only by consuming the retained reserve.
- `HOLD_INSUFFICIENT`: observed capacity cannot cover the run.
- `HOLD_UNKNOWN`: capacity cannot be established.
- `HOLD_PROVIDER_UNAVAILABLE`: the provider has refused or disabled execution.
- `AUTHORITY_REQUIRED_PAID`: paid execution could cover the run but lacks explicit authority.
- `AUTHORITY_CONSUMED`: the one-shot paid authorization has already been used.

Only `PROCEED` permits automatic invocation. Paid execution is never automatic. A paid authorization records an identifier, human authority, authorization time, expiry, exact execution ID, plan digest, billing scope, and maximum paid minutes; it never reduces to a Boolean. The dispatcher must atomically append the authorization ID to its durable consumption ledger before launch, then retain the provider receipt. Reassessment receives the consumed-ID ledger and refuses replay. When price data is available, also show the bounded monetary estimate to the principal before authorization. Minimize or batch the plan and reassess when held. If a local, clean-host, or self-hosted substitute exercises the real product boundary, use it and record the precise hosted-provider guarantee still absent.

## GitHub Actions

For private repositories, inspect the account or organization Actions allowance through the current GitHub billing UI or billing API before triggering GitHub-hosted runners. Record when the value was observed and when the allowance is expected to refresh. If the available credential cannot read billing data, report `unknown`; do not infer capacity from repository access.

Expand every workflow trigger and matrix job. In particular, a push to a pull-request branch can create both a `push` run and a `pull_request` run. Keep both only when both trigger paths are part of the acceptance claim.

GitHub-hosted execution, public-repository treatment, larger runners, and self-hosted runners have different billing and operational boundaries. Consult current official GitHub documentation when constructing the snapshot. A red workflow with no executed steps and a billing or spending-limit refusal is evidence that GitHub did not run the test, not evidence that the candidate failed it.
