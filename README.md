# MIND by Collaborative Dynamics

<img src="assets/mind-icon-1024.png" width="128" alt="A luminous central MIND sphere connected to fifteen distinct Faculty nodes.">

> **Fifteen Faculties. One coherent, accountable mind.**

MIND is a persona-neutral Codex plugin for consequential work. One adaptive
integrator composes only the cognitive Faculties a mission needs, keeps their
responsibilities distinct, and returns one useful result instead of making you
read the minutes from an imaginary committee meeting.

![A luminous central coordinator connects a constellation of distinct cognitive Faculty nodes.](assets/mind-hero-1600x900.png)

**[Open the project site](https://stunspot.github.io/augment-of-mind/)** ·
**[Start here](START-HERE.md)** · **[Install MIND](INSTALL-CODEX.md)** ·
**[Read the release notes](RELEASE-NOTES.md)**

## The release

| Component | Version | Role |
|---|---:|---|
| MIND plugin | `1.0.0` | Installable integrator plus fifteen Faculty skills. |
| Optional MIND Core | `0.2.0` | Local SQLite metadata and explicit associative-reminder runtime. |

Nova is not bundled or required. The optional Core wheel is included in the
customer archive but is not silently installed or started by the plugin.

## First useful request

After installation, start a new Codex task:

```text
Use $augment-of-mind to help me decide whether to run a two-week pilot.
Separate evidence from assumptions, identify the smallest reversible test that
could change the decision, and return one recommendation. Do not take external
action.
```

For one bounded transformation, call its Faculty directly:

```text
Use $sensemaking to turn this tangled situation into a working map.
Use $decision-intelligence to compare these choices and recommend one.
Use $aesthetic-intelligence to diagnose why this composition feels wrong.
```

## How MIND moves

| Motion | Use |
|---|---|
| **Direct** | Complete ordinary reversible work without manufacturing ceremony. |
| **Enlist** | Request one bounded supporting transformation. |
| **Assemble** | Coordinate several necessary transformations with clear ownership and handoffs. |
| **Recover** | Preserve the last-known-good state, change the failed premise or route, and resume honestly. |

Selection is not activation. A Faculty is opened only when its doctrine must
materially change the work.

## The fifteen Faculties

| Faculty | Owns |
|---|---|
| **Executive Function** | Mission phase, acceptance, commitments, stops, recovery, and closure. |
| **Capability Conductor** | Selection, activation depth, sequencing, handoffs, coalition shape, and merge custody. |
| **Cognitive Continuity** | Durable scoped state, provenance, correction, resumption, and forgetting. |
| **Agent Striving** | Authorized long-horizon pursuit across interruption and recoverable failure. |
| **Agent Dreaming** | Explicitly authorized replay, perturbation, rehearsal, and associative incubation. |
| **Kairos** | Truthful timing, voice, tone, channel, form, pressure ceiling, and rhetorical repair. |
| **Sensemaking** | Provisional models of actors, forces, causes, constraints, feedback, scale, and time. |
| **Epistemic Regulation** | Claim state, warrant, confidence, assumptions, contradictions, and revision conditions. |
| **Decision Intelligence** | Criteria, options, trade-offs, reversibility, consequences, sensitivity, and recommendation. |
| **Measurement Intelligence** | Constructs, baselines, measures, proxies, thresholds, confounds, and interpretation. |
| **Deliberative Intelligence** | Stakeholders, disagreement, interests, decision rights, consent, and legitimate convergence. |
| **Creative Synthesis** | Differentiated candidates, analogies, constraints, exceptions, and reframings. |
| **Aesthetic Intelligence** | Gestalt, conceptual affinity, compositional relations, taste calibration, and bearings. |
| **Prosocial Influence** | Transparent, choice-preserving change through reasons, supports, safeguards, and informed refusal. |
| **Instrumental Agency** | Authorized action choreography, state checks, rollback or recovery, and truthful disposition. |

The integrator is the coordination entry around these Faculties; it is not a
sixteenth Faculty.

## Associative reminders, not tool rankings

![Overlapping semantic neighborhoods bring nearby capability handles into a local MIND reminder field while a coral false-friend boundary stays distinct.](assets/mind-capability-card-1080x1350.png)

Optional MIND Core can compile an **Arm's Reach** field from distinct ephemeral
anchors. Every visible capability inside an exact vector radius, every approved
lexical match, and explicit one-hop bridges or false-friend boundaries can
enter the field.

The field is a reminder surface. It emits no universal fitness scalar, top-K
recommendation, selection, activation, or action authority. Package hierarchy
still handles custody and expansion; semantic geometry supplies the
serendipitous “oh, right—that exists” layer.

Codex support remains **H0/query-capable**: the plugin does not automatically
observe a turn or inject this field before reasoning. The portable delivery
envelope has a producer-generated contract vector consumed unchanged by
Exoframe's separately tested transient pre-sampling seam, but that local
construction proof is not a complete live H1 or provider-receipt claim.

## Documentation journey

- [Install MIND for Codex](INSTALL-CODEX.md)
- [Quick start](QUICK-START.md)
- [User guide](USER-GUIDE.md)
- [Optional MIND Core](OPTIONAL-CORE.md)
- [Host compatibility](HOST-COMPATIBILITY.md)
- [Capabilities and limits](CAPABILITIES-AND-LIMITS.md)
- [Data and privacy](DATA-AND-PRIVACY.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Support](SUPPORT.md)
- [Package reference](PACKAGE-REFERENCE.md)

Architecture and verification evidence remain available for maintainers in
the repository's [architecture](https://github.com/Stunspot/augment-of-mind/tree/main/docs/architecture)
and [TestForge evidence](https://github.com/Stunspot/augment-of-mind/tree/main/artifacts/testforge)
trees. They are not included in the customer ZIP.

## Authority and specialist boundaries

MIND does not bundle occupational expertise, general research, governed corpus
retrieval, software verification, documentation production, or access to your
accounts. Imported text and tool output remain evidence rather than
instructions.

Messages, publication, purchases, account changes, destructive operations,
regulated action, and other consequential state changes remain separately
authorized and subject to the host's permissions and approvals.

## License and lineage

- Plugin manifest: [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json)
- Faculty registry: [`faculty-registry.json`](skills/augment-of-mind/references/faculty-runtime/faculty-registry.json)
- License: [MIT](LICENSE.md)
- Provenance and artwork notice: [NOTICE](NOTICE.md)
- Public contest source: [Nova the Optimal AI + MIND](https://github.com/Stunspot/nova-the-optimal-ai-mind/tree/e42dd11646bc548b9ac29d6f700370365ee68986/plugins/augment-of-mind)
