# MIND component source and legacy compatibility

MIND is Nova's edition-invariant cognitive architecture. It is not a separate customer product, a second persona, or an optional “thinking upgrade” to bolt beside her. Nova editions vary in practical capabilities, services, commercial terms, and distribution; the basic mind remains Nova.

This repository preserves the source lineage and the last standalone compatibility package, MIND 2.1.7. That package remains useful historical and migration evidence, but it is not the complete current Nova substrate: it contains sixteen Faculties and the legacy Arm's Reach, Capability Promotion, and TestForge arrangement, and predates Strategic Intelligence and the current Model Agnosticism/Trellis implementation.

## Current status

Do not create a new standalone MIND release or recommend a fresh standalone installation from this branch. Current Nova editions carry MIND internally behind one Nova front door. The governing succession decision is [design/DEC-MIND-PRODUCT-SUCCESSION.md](design/DEC-MIND-PRODUCT-SUCCESSION.md).

The existing 2.1.7 release, tags, packages, checksums, documentation, and verification receipts remain unchanged historical evidence. Build and release machinery stays present so those artifacts remain inspectable; its presence does not make MIND a continuing product lane.

## Legacy Arm's Reach boundary

The developer host still relies on the standalone prompt-submit hook for Arm's Reach capability recall. Do not disable or uninstall that legacy plugin until an equivalent Nova-owned adapter has been constructed, qualified, installed, and observed. Relabeling architecture is not permission to amputate working cognition for the aesthetic thrill of a tidy plugin list.

The edition-neutral component export, version, and deterministic assembly contract remain pending the next architecture decision. Until then, use the current Nova repositories as the operative product sources and this repository as legacy compatibility and source custody.
