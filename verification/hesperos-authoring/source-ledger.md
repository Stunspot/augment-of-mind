# Documentation source ledger

| Source | Custody | Use | Evidence state |
|---|---|---|---|
| `.codex-plugin/plugin.json` | Repository | Product identity, versions, presentation assets, repository and legal links | Source-verified |
| `.agents/plugins/marketplace.json` | Repository | Marketplace name, plugin source, availability, installation behavior | Source-verified |
| `skills/augment-of-mind/SKILL.md` | Repository | Integrator promise, motions, authority, orchestration, specialist boundaries | Source-verified |
| `skills/augment-of-mind/references/faculty-runtime/faculty-registry.json` | Repository | Exact fifteen-Faculty inventory | Source-verified |
| `skills/*/SKILL.md` | Repository | Faculty ownership descriptions | Source-verified |
| `mind_core/`, `pyproject.toml`, and `tests/` | Repository | Core version, commands, schema, persistence, security, H0, reminder-field behavior | Source-verified by 77 passing tests; fresh-package evidence remains a later gate |
| `docs/architecture/RELEASE-CONTRACT-v1.0.0.md` | Repository | Customer ZIP root, allowlist, exclusions, component split, release gates | Approved release contract |
| `docs/architecture/MIND-REMINDER-DELIVERY-PROTOCOL.md` | Repository | Portable delivery vocabulary and H0/H1 evidence boundary | Source-verified architecture; not live-provider proof |
| [OpenAI: Build plugins](https://developers.openai.com/plugins/build/plugins) | Official host documentation | Plugin packaging, marketplace source, install/new-session path | Source-verified for current documented surface |
| [OpenAI: Use plugins](https://learn.chatgpt.com/docs/plugins) | Official host documentation | Supported Codex surfaces and user flow | Source-verified for current documented surface |
| Current Collaborative Dynamics release brief | Owner direction | One complete ZIP and Pages site with icon, hero, and capability-card roles | Reported requirement |
| [Public Build Week lineage](https://github.com/Stunspot/nova-the-optimal-ai-mind/tree/e42dd11646bc548b9ac29d6f700370365ee68986/plugins/augment-of-mind) | Public source | Product lineage only | Source-verified provenance; not current release evidence |

## Conflict handling

The plugin and optional Core have different version numbers and are documented
as separate objects. A host-readable skill file is not described as installed,
discoverable, invoked, or healthy without the corresponding host evidence.
Local construction and static Pages evidence are not described as publication
or live browser behavior.
