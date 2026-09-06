**DEPENDENCY AND ENVIRONMENT GUIDE**





# METADATA
<details>
<summary>Document code, status, review date, and usage instructions.</summary>

| Field                   | Value                                                    |
| :---------------------- | :------------------------------------------------------- |
| **Code**                | `DEP`                                                    |
| **Status**              | Live                                                     |
| **Last reviewed**       | 2026-09-06                                               |
| **Source of truth for** | Human-readable dependency inventory and environment setup |
| **Parent**              | [`PLN`](PLN_plan.md)                                     |
| **Related**             | [`CTR`](CTR_contracts.md) · [`RDM`](../README.md)        |

**For the team.** This document lists every direct downloadable Python dependency currently
declared by the application and separates it from packages planned for later work. The executable
dependency source remains `pyproject.toml`; that file wins if the two disagree.

**For the assistant.** Any dependency change must update `pyproject.toml` and this inventory in the
same change. A planned package must not be presented as installed until it is declared and passes
the clean-environment checks in [`DEP_S4`](#4-installation-and-verification).

</details>

---





# 1. SCOPE
## 1.1. Included Dependencies
This guide covers Python, the build backend, direct runtime packages, development packages, and the
three packages already named by [`PLN_S4.2`](PLN_plan.md#42-t02--pin-the-environment). Transitive
packages are resolved by the package installer and are not maintained as a second hand-written
list.

The package list was checked against `pyproject.toml` on **2026-09-06**. Version ranges are the
current repository contract. They are not an exact lock file.




## 1.2. Not Included
AWS credentials, Bedrock model access, environment variables, classifier weights, MediaPipe
`.task` assets, recordings, and third-party reference-repository clones are not Python
dependencies. Model assets remain a separate `T1.2` download with a fixed URL and checksum once
that task selects the artifact.

---





# 2. PYTHON ENVIRONMENT
## 2.1. Required Interpreter
The application requires **Python 3.11 or newer and earlier than 3.14**, as declared by
`pyproject.toml`. Python **3.12** is the recommended team baseline. Apple Command Line Tools Python
3.9 does not satisfy the project constraint.

Before installing, this command must report Python 3.11, 3.12, or 3.13:

```bash
python --version
```




## 2.2. macOS and Linux
An incompatible existing `.venv` must be moved or removed manually before these commands are run.
The commands intentionally install from `pyproject.toml`, not from an independently maintained
package list.

On macOS with Homebrew, a missing Python 3.12 interpreter can be installed first [S5]:

```bash
brew install python@3.12
```

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```




## 2.3. Windows PowerShell
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The standard-library `venv` module creates an isolated environment whose interpreter and installed
packages are separate from the base interpreter [S4].

---





# 3. DOWNLOADABLE DEPENDENCIES
## 3.1. Build Dependency
| Package     | Declared constraint | Purpose                         |
| :---------- | :------------------ | :------------------------------ |
| `hatchling` | `>=1.26,<2`         | PEP 517 build and wheel backend |




## 3.2. Runtime Dependencies Declared Now
| Package             | Declared constraint | Application purpose              |
| :------------------ | :------------------ | :------------------------------- |
| `boto3`             | `>=1.35,<2`         | AWS Bedrock client               |
| `fastapi`           | `>=0.115,<1`        | HTTP and WebSocket application   |
| `langgraph`         | `==1.2.11`          | Bounded agent graph              |
| `numpy`             | `>=1.26,<3`         | Numeric recognition operations   |
| `pydantic`          | `>=2.9,<3`          | Strict contracts and settings    |
| `pydantic-settings` | `>=2.6,<3`          | Environment-backed configuration |
| `uvicorn`           | `>=0.30,<1`         | ASGI server                      |




## 3.3. Development Dependencies Declared Now
| Package          | Declared constraint | Development purpose          |
| :--------------- | :------------------ | :--------------------------- |
| `httpx`          | `>=0.27,<1`         | API tests                    |
| `mypy`           | `>=1.13,<2`         | Static type checks           |
| `pytest`         | `>=8.3,<9`          | Test runner                  |
| `pytest-asyncio` | `>=0.24,<1`         | Async test support           |
| `ruff`           | `>=0.8,<1`          | Linting and formatting       |




## 3.4. Planned Dependencies Not Yet Declared
These packages are downloadable, but they are **not installed by the current project command**.
Their exact candidate pins were checked on 2026-09-06 and must pass `T0.2` compatibility checks
before entering `pyproject.toml`.

1. **`mediapipe==1.0.1`**
   Candidate for MediaPipe Tasks perception work [S1].
2. **`pose-format==0.14.1`**
   Candidate pose container. Only the base package is permitted; the `pose-format[mediapipe]`
   extra must never be installed because
   [`SPR`](../ref_repo/translation/sign-pose/SPR_sign_pose_report.md) records the dependency
   collision [S2].
3. **`spoken-to-signed==0.0.2`**
   Candidate for the reverse-direction pipeline in WP6, not the stage ⑥ assembler [S3].

> **Warning:** Directly installing the three planned packages outside `pyproject.toml` creates an
> environment the repository cannot reproduce. They remain deferred until their owning tasks add
> and verify them.

---





# 4. INSTALLATION AND VERIFICATION
## 4.1. Current Application
After activation and installation, the environment passes when all commands exit successfully:

```bash
python --version
python -m pip check
python -c "import boto3, fastapi, langgraph, numpy, pydantic, pydantic_settings, uvicorn"
python -m pytest
python -m ruff check .
python -m mypy
```




## 4.2. Future Perception Gate
After `T0.2` declares the perception packages, its additional clean-environment smoke check is:

```bash
python -c "import mediapipe; import pose_format"
```

The `pose-format` base install is the required variant. The MediaPipe extra is excluded.




## 4.3. Reproducibility Lock
`pyproject.toml` remains the editable declaration and compatibility source. The generated
`pylock.toml` is the exact PEP 751 installation artifact for the verified CPython 3.12, macOS ARM64
development environment. It pins all 62 runtime, development, and transitive packages to exact
wheel URLs and SHA-256 hashes. Pip currently guarantees a generated lock only for the Python
version and platform on which it was resolved.

Regenerate the dependency-only lock after any declared dependency change:

```bash
python -m pip lock --only-deps '.[dev]' -o pylock.toml --exists-action w
```

The project is deliberately excluded from the hash lock because an editable local directory has
no single archive hash. Reproduce the verified environment by installing the lock first, then the
local project without allowing a second dependency resolution:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r pylock.toml
python -m pip install --no-deps -e .
python -m pip check
python -m pytest
python -m ruff check src tests main.py
python -m mypy src
```

The lock was generated and installed successfully with `pip==26.2.1`; pip still labels its
`lock` command and `pylock.toml` installation support experimental. The build-system requirement
for `hatchling` remains bounded in `pyproject.toml` and is resolved in pip's isolated build
environment. A deployment lock for another OS, architecture, or Python minor version must be
generated and tested on that target.

---





# 5. SOURCES
1. **`[S1]`**
   *Source:* [MediaPipe on PyPI](https://pypi.org/project/mediapipe/) — published package version
   and supported distributions checked 2026-09-06.
   *Reliability:* Official package index metadata supplied by the publisher.
2. **`[S2]`**
   *Source:* [pose-format on PyPI](https://pypi.org/project/pose-format/) — published base package
   and optional extras checked 2026-09-06.
   *Reliability:* Official package index metadata supplied by the publisher.
3. **`[S3]`**
   *Source:* [spoken-to-signed on PyPI](https://pypi.org/project/spoken-to-signed/) — published
   package version checked 2026-09-06.
   *Reliability:* Official package index metadata supplied by the publisher.
4. **`[S4]`**
   *Source:* [Python `venv` documentation](https://docs.python.org/3/library/venv.html) — isolated
   environment creation and activation.
   *Reliability:* Official Python documentation.
5. **`[S5]`**
   *Source:*
   [Homebrew `python@3.12` formula](https://formulae.brew.sh/formula/python@3.12) — macOS
   installation command and maintained Python 3.12 package.
   *Reliability:* Official Homebrew formula index.

---





# 6. CHANGE LOG
2. **2026-09-06** · *Author:* Codex (GPT-5)
   *Change:* Added and clean-environment tested the PEP 751 `pylock.toml` dependency lock for
   CPython 3.12 on macOS ARM64, including the locked-install and no-dependency editable-project
   workflow and its current platform/build-system limitations.
1. **2026-09-06** · *Author:* Codex (GPT-5)
   *Change:* Created the dependency inventory, Python 3.12 virtual-environment instructions,
   current runtime and development package lists, planned perception and reverse-direction
   packages, verification commands, and the remaining exact-lock requirement.
