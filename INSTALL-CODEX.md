# Install MIND for Codex

Goal: make MIND `1.0.0` discoverable as an installed Codex plugin.

Audience: a Codex or ChatGPT desktop user who can configure a plugin
marketplace.

## Before you begin

- Use Codex in the ChatGPT desktop app or Codex CLI. Plugins are not currently
  available in the Codex IDE extension.
- You need Git for the online route, or the release ZIP and its `.sha256`
  sidecar for the offline route.
- Python 3.11 or newer is required only for the extracted-tree verifier and
  optional MIND Core. It is not required to run the skills-only plugin.
- Installation changes only your local Codex plugin configuration and cache.
  It does not install MIND Core.

## Install from GitHub

After release `v1.0.0` is published, add its pinned marketplace source:

```powershell
codex plugin marketplace add Stunspot/augment-of-mind --ref v1.0.0
```

Expected result: Codex records the `collaborative-dynamics` marketplace without
an error.

Then:

1. Open Codex CLI and enter `/plugins`, or open **Plugins** in the ChatGPT
   desktop app while using Codex.
2. Select the **Collaborative Dynamics** marketplace.
3. Open **MIND by Collaborative Dynamics** and install it.
4. Confirm that it appears in the installed list and is enabled.
5. Start a new task. Installed skills are loaded at the new-task boundary.

Completion proof: the new task exposes `$augment-of-mind` and the Faculty
skills, and the [quick-start request](QUICK-START.md) produces a response.

## Install from the release ZIP

1. Download `augment-of-mind-v1.0.0.zip` and its `.sha256` sidecar from the
   same GitHub release.
2. Verify the ZIP's SHA-256 value against the sidecar. On Windows:

   ```powershell
   Get-FileHash .\augment-of-mind-v1.0.0.zip -Algorithm SHA256
   ```

   On macOS use `shasum -a 256 augment-of-mind-v1.0.0.zip`; on Linux use
   `sha256sum augment-of-mind-v1.0.0.zip`. The reported value must exactly
   match the value in the sidecar.
3. Extract it. The result must contain one directory named
   `augment-of-mind-v1.0.0`.
4. If Python 3.11 or newer is available, run the stronger extracted-tree
   verifier from that directory:

   ```powershell
   python .\verify-release.py .
   ```

   This check validates every packaged path and component hash. A skills-only
   user without Python can still install the ZIP whose archive hash passed the
   previous step.
5. Add the extracted directory as a local marketplace:

   ```powershell
   codex plugin marketplace add C:\path\to\augment-of-mind-v1.0.0
   ```

6. Install MIND from the **Collaborative Dynamics** marketplace using the same
   plugin-browser steps, then start a new task.

## Update or remove

To refresh configured Git-backed marketplaces:

```powershell
codex plugin marketplace upgrade collaborative-dynamics
```

Use the plugin browser to uninstall or disable MIND. To stop tracking its
marketplace as well:

```powershell
codex plugin marketplace remove collaborative-dynamics
```

Removing the plugin does not delete an optional MIND Core database or Python
environment. Those are separately owned local files.

## If the result differs

Do not hand-edit `config.toml` as the first move. Preserve the exact command
output, run `codex plugin marketplace list`, and follow
[Troubleshooting](TROUBLESHOOTING.md#the-marketplace-does-not-appear).

Official host reference: [OpenAI plugin packaging and local marketplaces](https://developers.openai.com/plugins/build/plugins).
