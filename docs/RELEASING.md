# OctoFlow Release Process & Maintainer Guide

**Version:** 1.0  
**Target:** Maintainers and Repository Owners  
**Security Standard:** OIDC Trusted Publishing (No Stored Secrets)  

---

## 1. Overview & Release Architecture

OctoFlow uses a fully automated, cryptographically secure release pipeline powered by GitHub Actions and PyPI Trusted Publishing (OIDC).

```
   [Owner CLI]
  scripts/release.py bump <patch|minor|major|X.Y.Z>
        │
        ▼
  git commit ("chore(release): bump version to X.Y.Z")
        │
        ▼
  git tag vX.Y.Z && git push origin vX.Y.Z
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ GitHub Actions Release Pipeline (.github/workflows/release) │
│                                                             │
│  1. Fast Test Suite (Linux & macOS • Python 3.10 - 3.13)    │
│                     │                                       │
│                     ▼                                       │
│  2. Build Wheel + Sdist + CycloneDX SBOM                    │
│     Clean-room verify: scripts/verify_wheel.sh (Ubuntu)     │
│                     │                                       │
│                     ▼                                       │
│  3. Cross-Platform Clean-Room Check (macOS)                 │
│                     │                                       │
│                     ▼                                       │
│  4. Publish to TestPyPI (Automated via OIDC)                │
│                     │                                       │
│                     ▼                                       │
│  5. Publish to PyPI (Gated on manual approval in GitHub UI) │
│                     │                                       │
│                     ▼                                       │
│  6. Create GitHub Release (Attach Wheel, Sdist, SBOMs)      │
└─────────────────────────────────────────────────────────────┘
```

### Why No API Tokens in GitHub Secrets?
OctoFlow enforces PyPI **Trusted Publishing** via OpenID Connect (OIDC). Short-lived, cryptographic identity tokens are exchanged directly between GitHub Actions runners and PyPI for each release job. No permanent API keys or account passwords ever exist in repository secrets, eliminating supply-chain credential theft vectors.

---

## 2. One-Time Setup for Repository Owner

Before cutting the first public release, the repository owner must configure PyPI Trusted Publishing and GitHub Environments.

### 2.1 TestPyPI Trusted Publisher Configuration
1. Log in to [TestPyPI](https://test.pypi.org/).
2. Navigate to **Account Settings** -> **Publishing**.
3. Under **Add a publisher**, choose **GitHub**:
   - **PyPI Project Name:** `octoflow`
   - **Owner:** `<github-owner-or-org>`
   - **Repository name:** `<repository-name>`
   - **Workflow name:** `release.yml`
   - **Environment name:** `testpypi`
4. Click **Add publisher**.

### 2.2 Production PyPI Trusted Publisher Configuration
1. Log in to [PyPI](https://pypi.org/).
2. Navigate to **Account Settings** -> **Publishing**.
3. Under **Add a publisher**, choose **GitHub**:
   - **PyPI Project Name:** `octoflow`
   - **Owner:** `<github-owner-or-org>`
   - **Repository name:** `<repository-name>`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Click **Add publisher**.

### 2.3 GitHub Environments & Manual Protection Rules
1. In your GitHub repository, navigate to **Settings** -> **Environments**.
2. Create environment `testpypi`:
   - No approval required (automatic publication for verification).
3. Create environment `pypi`:
   - Enable **Required reviewers**.
   - Select your GitHub user account as the required reviewer.
   - Set deployment branch to **Selected tags** (`v*.*.*`).

---

## 3. Release Rehearsal Procedure (TestPyPI First)

Always test distribution packaging and installation against TestPyPI before deploying to production PyPI:

1. **Local Dry-Run Verification:**
   ```bash
   # Run release script dry run
   python scripts/release.py bump patch --dry-run

   # Build distribution and run clean-room verification locally
   make build
   bash scripts/verify_wheel.sh
   ```

2. **TestPyPI Verification:**
   Once pushed, observe the `publish-testpypi` job in GitHub Actions. After it completes, verify the release in a clean temporary virtual environment:
   ```bash
   TEST_DIR=$(mktemp -d)
   python3 -m venv "$TEST_DIR/venv"
   "$TEST_DIR/venv/bin/pip" install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple octoflow
   "$TEST_DIR/venv/bin/octoflow" --help
   "$TEST_DIR/venv/bin/octoflow" doctor
   rm -rf "$TEST_DIR"
   ```

---

## 4. Step-by-Step Production Release Checklist

Follow this exact sequence when releasing a new version:

### Step 1: Ensure Working Tree is Clean
```bash
git checkout main
git pull origin main
git status
```

### Step 2: Bump Version and Update Changelog
```bash
# Bump patch (0.2.0 -> 0.2.1) or minor (0.2.0 -> 0.3.0) or explicit version
python scripts/release.py bump minor
```
This updates `pyproject.toml` and moves entries under `## [Unreleased]` into a dated release section in `CHANGELOG.md`, creating a release preparation commit.

### Step 3: Run Local Validation Suite
```bash
make test-fast
make build
bash scripts/verify_wheel.sh
```

### Step 4: Push Commit and Create Tag
```bash
# Inspect the release commit
git show HEAD

# Push the release commit to main
git push origin main

# Tag the release (Owner's prerogative; script never tags automatically)
git tag v0.3.0
git push origin v0.3.0
```

### Step 5: Monitor Release Pipeline
1. Open the GitHub Actions tab in your repository.
2. Observe the running `Release` workflow for tag `v0.3.0`.
3. Verify that `test`, `build`, `verify-macos`, and `publish-testpypi` succeed.

### Step 6: Approve Production Deployment
1. When the `publish-pypi` job pauses, click **Review deployments**.
2. Select the `pypi` environment and click **Approve and deploy**.
3. Observe successful publication to `https://pypi.org/project/octoflow/`.

### Step 7: Verify Live PyPI Installation
```bash
pip install --upgrade octoflow
octoflow --help
octoflow doctor
```

---

## 5. Rollback & Yank Procedures

If a critical flaw or security vulnerability is discovered immediately post-release:

### 5.1 Yanking a Release on PyPI
*Do not attempt to re-upload files with the same version number; PyPI rejects duplicate filenames.*
1. Log in to [PyPI](https://pypi.org/manage/project/octoflow/releases/).
2. Click **Options** on the defective version.
3. Select **Yank release**.
4. Enter a reason (e.g., "Critical regression in gate surprise evaluation; upgrade to v0.3.1").
5. Click **Yank release**.
*(Yanked releases remain installable for pinned lockfiles but will not be chosen by pip solvers for new installs).*

### 5.2 Cutting an Emergency Patch
1. Run `python scripts/release.py bump patch`.
2. Commit the fix and bump.
3. Push commit and new tag `v0.3.1`.
4. Follow standard release steps above.

### 5.3 Retracting a GitHub Release
1. Go to repository **Releases** page.
2. Edit the affected release tag and mark as **Pre-release** or delete the release notes.
3. Provide an advisory notice pointing users to the patched release.
