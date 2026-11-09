# OctoFlow Repository Owner Configuration Checklist

This checklist contains administrative settings that cannot be configured directly via git files and must be enabled in the GitHub repository web settings by the repository owner.

---

## 1. Security & Vulnerability Reporting

- [ ] **Enable Private Vulnerability Reporting:**
  - Navigate to **Settings > Code security and analysis**.
  - Under **Private vulnerability reporting**, click **Enable**.
  - *Rationale:* Allows researchers and users to report security findings privately via GitHub Security Advisories rather than opening public issues.
- [ ] **Enable Dependabot Alerts:**
  - Under **Code security and analysis**, ensure **Dependabot alerts** and **Dependabot security updates** are enabled.
- [ ] **Enable Secret Scanning:**
  - Under **Code security and analysis**, enable **Secret scanning** and **Push protection** to prevent inadvertent credential commits.

---

## 2. Community & Discussions

- [ ] **Enable GitHub Discussions:**
  - Navigate to **Settings > General**.
  - In the **Features** section, check **Discussions**.
  - Open the **Discussions** tab in your repository and set up standard categories:
    - `Announcements` (maintainer announcements and release notes)
    - `Q&A / Help` (user setup questions and local inference assistance)
    - `Ideas & Proposals` (RFCs, feature proposals, and provider suggestions)
    - `Show and Tell` (sharing custom 8-arm specialist guilds)
- [ ] **Verify Issue Forms:**
  - Navigate to **Issues > New issue** and confirm that GitHub renders the custom issue forms from `.github/ISSUE_TEMPLATE/` (`bug_report.yml`, `feature_request.yml`, `provider_request.yml`) and that blank issues are disabled via `config.yml`.

---

## 3. Branch Protection (`main` / `master`)

- [ ] **Configure Branch Protection Rule:**
  - Navigate to **Settings > Branches** and click **Add branch protection rule** (Branch name pattern: `main` or `master`).
  - Check **Require a pull request before merging**.
  - Check **Require status checks to pass before merging**.
  - Check **Require branches to be up to date before merging**.
  - Select the following mandatory status checks from the search list:
    - `Lint & Style (Ruff)`
    - `Gradual Typecheck (mypy)`
    - `Generated Reference Documentation Staleness Check`
    - `Documentation Integrity & Link Check`
    - `Base Package Unit Tests (No Torch/ML)`
    - `WebGL Visualizer Quality Gates & Dist Sync`
  - Check **Do not allow bypassing the above settings**.

---

## 4. Maintainer Account Security

- [ ] **Enable Two-Factor Authentication (2FA):**
  - Ensure all maintainer accounts have hardware security key or authenticator app 2FA enabled.
  - If hosted under a GitHub Organization, enforce **Require two-factor authentication for everyone in the organization**.

---

## 5. Repository Metadata & Discovery

- [ ] **Set Repository Description:**
  - Set description to:  
    `A local-first coding swarm that spends tokens only when something changes, and shows you where every token went.`
- [ ] **Set Topics:**
  - Add repository tags:  
    `ai-agents`, `multi-agent`, `octopus-brain`, `local-first`, `developer-tools`, `python`, `active-inference`, `mcp-server`
- [ ] **Set Custom URLs:**
  - If a demo website or visualizer is deployed, configure the website URL in the repository header.

---

## 6. Repository Placeholders to Fill

Before publishing or inviting public contributors, replace the following placeholder tokens:

| File | Placeholder Token | Replacement Target |
| :--- | :--- | :--- |
| [`.github/CODEOWNERS`](../.github/CODEOWNERS) | `@TODO_MAINTAINER_HANDLE` | Your GitHub username or team handle (e.g. `@sachinrk`) |
| [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | `[TODO: INSERT OWNER/MAINTAINER EMAIL HERE]` | Your public contact or conduct reporting email |
| [`SECURITY.md`](../SECURITY.md) | `[TODO: INSERT SECURITY EMAIL HERE]` | Your private security contact address |
| [`SUPPORT.md`](../SUPPORT.md) | `TODO_OWNER_OR_ORG` | Your GitHub organization or username in URLs |
| [`.github/ISSUE_TEMPLATE/config.yml`](../.github/ISSUE_TEMPLATE/config.yml) | `TODO_OWNER_OR_ORG` | Your GitHub organization or username in URLs |

---

## 7. PyPI & Release Automation Setup

See [`docs/RELEASING.md`](./RELEASING.md) for complete instructions:

- [ ] **Configure PyPI Trusted Publishing:**
  - Set up GitHub OIDC trusted publishing on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/) for workflow `release.yml`.
- [ ] **Create GitHub Environments:**
  - Navigate to **Settings > Environments** and configure `testpypi` (auto) and `pypi` (manual approval required).
