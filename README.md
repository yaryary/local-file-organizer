# Local AI File Organizer

A Python project for building a local, privacy-first file organizer powered by Ollama. The intended workflow is to inspect files, propose categories and names, preview changes, and apply only approved operations.

The project is being built incrementally. So far, it includes a local Ollama connection and a read-only directory scanner. The scanner collects file metadata, skips excluded entries, and checks a configurable entry limit. Classification and filesystem changes are not implemented yet.

## Current status

### M1 — Read-only scanner

`scanner.py` scans a selected directory and returns metadata for regular files.

It:

- Collects filenames, extensions, sizes, relative paths, and modification timestamps.
- Scans only the selected directory, without entering subdirectories.
- Skips hidden entries, symbolic links, and non-file entries.
- Rejects missing, non-directory, and symbolic-link scan roots.
- Uses a configurable entry limit, with a default of 100.
- Counts all immediate entries toward the limit, including entries that are skipped.
- Checks the limit before sorting entries or collecting file metadata.
- Returns records in filename order without changing any files.
- Prints a warning and continues scanning when an eligible file’s metadata cannot be read.

Manual scanner tests have passed. The scanner now also has 22 automated regression tests using Python’s `unittest` module and isolated temporary fixtures. All 22 tests passed locally and in a macOS GitHub Actions run. CI failure detection was verified by temporarily introducing an incorrect assertion, confirming the workflow failed, then restoring the assertion and confirming it passed again.

The current `main.py`:

- Sends a JSON chat request to Ollama using Python's standard library.
- Uses `qwen3.5:9b` with streaming and thinking disabled in the request.
- Extracts and validates a nonempty text reply.
- Reports connection failures and HTTP errors.
- Includes timeout and response-parsing handling; those failure cases have not been tested yet.

## Tested environment

| Component           | Version / configuration                             |
| ------------------- | --------------------------------------------------- |
| Operating system    | macOS                                               |
| Hardware            | MacBook Air 15-inch, Apple M4, 24 GB unified memory |
| Python              | 3.14.4                                              |
| Ollama              | 0.40.9                                              |
| Model               | `qwen3.5:9b`                                        |
| Ollama installation | Homebrew                                            |
| API endpoint        | `http://localhost:11434/api/chat`                   |
| Request settings    | `"stream": false`, `"think": false`                 |

The table records the local setup used during manual testing. Automated scanner tests also passed locally with Python 3.14.4 and in GitHub Actions with CPython 3.14.10 on a `macos-latest` runner. These results are not a tested compatibility range. The thinking setting was included in the request; its behavior was not independently evaluated.

## Requirements

- macOS with Homebrew installed for the setup below.
- Python 3.14 for the documented scanner setup. Automated scanner tests have passed with Python 3.14.4 locally and CPython 3.14.10 in CI. Older Python versions have not been verified.
- Ollama and the `qwen3.5:9b` model.
- Internet access for initial installation and model download.

The current Python scripts and scanner tests use only standard-library modules. No third-party Python packages are required. Ollama and the model are needed for the connection demo, but not for the scanner or scanner tests.

## Setup

### 1. Open the project directory

If you already have the project locally:

```bash
cd /path/to/local-file-organizer
```

Replace the path with your actual project location. The directory should contain `main.py`.

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If `.venv` already exists, only run the activation command. The `(.venv)` prefix indicates that the environment is active.

### 3. Install and start Ollama

If Ollama is not installed:

```bash
brew install ollama
```

Start the Homebrew-managed server:

```bash
brew services start ollama
```

This setup runs Ollama as a background service. Do not also start a separate `ollama serve` process on the same port.

### 4. Download the model

```bash
ollama pull qwen3.5:9b
```

This step downloads the model. Subsequent inference requests use the local server and installed model.

### 5. Check the configuration

The working configuration in `main.py` is:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"
```

The request payload includes:

```python
"stream": False,
"think": False,
```

## Run

From the project directory, with the virtual environment active:

```bash
python3 main.py
```

Example output:

```text
Model: qwen3.5:9b
Reply: Message received.
```

The exact response wording can vary. A successful test requires a nonempty reply, not an exact sentence match.

`main.py` sends a fixed connection-test prompt. It does not call the scanner or modify files.

### Run the scanner

Create a disposable folder at `sandbox/input` and add a few synthetic test files. Then run:

```bash
python3 scanner.py
```

The scanner prints skipped entries and the metadata records it collects. Ollama does not need to be running for this.

The `sandbox/` directory is ignored by Git, so it must be created locally.

## Manage the Ollama server

These commands apply to the Homebrew-managed installation used for this project:

| Action                | Command                        |
| --------------------- | ------------------------------ |
| Start the server      | `brew services start ollama`   |
| Stop the server       | `brew services stop ollama`    |
| Restart the server    | `brew services restart ollama` |
| Inspect services      | `brew services list`           |
| List installed models | `ollama list`                  |
| Show Python version   | `python3 --version`            |
| Show Ollama version   | `ollama --version`             |

`ollama stop qwen3.5:9b` unloads the model; it does not stop the API server. A later request can load the model again. Use `brew services stop ollama` when testing server unavailability.

## Manual test results

Test date: October 27, 2026.

These tests were performed manually from Terminal using `python3 main.py`. They are not an automated test suite.

| Test                   | Setup                                                                             | Observed result                                       | Status |
| ---------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------- | ------ |
| Successful request     | Server available; model set to `qwen3.5:9b`                                       | Printed the model name and `Reply: Message received.` | Passed |
| Repeated request       | Run the script again with the same working configuration                          | Printed `Reply: I have received your message.`        | Passed |
| Server unavailable     | Stop the Ollama server, then run the script                                       | Printed the intended connection error                 | Passed |
| Recovery after restart | Restart the server, then run the script                                           | Printed `Reply: Message received.`                    | Passed |
| Invalid model name     | Temporarily set the model to `qwen3.5`, which was unavailable in the tested setup | Printed HTTP 404 and the model-not-found message      | Passed |

### Manual scanner tests

Test date: October 29, 2026.

These tests were run manually using synthetic files under `sandbox/`.

| Test                                                                   | Result                                            |
| ---------------------------------------------------------------------- | ------------------------------------------------- |
| Three entries with a limit of four                                     | Passed                                            |
| Three entries with a limit of three                                    | Passed                                            |
| Three entries with a limit of two                                      | Passed: expected error, with no partial inventory |
| Hidden entries, directories, and symbolic links count toward the limit | Passed                                            |
| Empty directory with a valid limit                                     | Passed: empty inventory                           |
| Zero and negative limits                                               | Passed: rejected                                  |
| String, float, and None limits                                         | Passed: rejected                                  |
| Boolean limit validation                                               | Expected error observed                           |
| Missing root, file used as root, and symbolic-link root                | Passed: rejected                                  |
| Ordinary inventory after restoring fixtures                            | Passed                                            |
| Nested files are not included                                          | Passed                                            |
| Empty regular file is included                                         | Passed                                            |

These manual results are retained as historical evidence. The scanner now also has an automated regression suite, documented below.

## Automated scanner tests

Verification date: November 1, 2026.

The scanner has 22 automated regression tests in `tests/test_scanner.py`, using Python's built-in `unittest` framework. Each test receives a fresh temporary directory with cleanup registered through `addCleanup`.

### Run locally

From the repository root:

```bash
python3 -m unittest discover -s tests -v
```

The suite uses synthetic temporary fixtures. It does not require Ollama, a downloaded model, network access, or an existing `sandbox/input` directory.

### Coverage scope

The suite checks:

- Empty directories and empty regular files.
- Below-limit, exact-limit, and over-limit behavior.
- Invalid limit values and types, including booleans.
- Missing, regular-file, and symbolic-link scan roots.
- Hidden entries, directories, and symbolic links counting toward the limit while being excluded from returned records.
- Nonrecursive scanning and filename ordering.
- The five expected metadata fields, extension normalization, byte sizes, relative paths, and modification timestamps.
- Preservation of fixture names, ordinary-file contents, modification times, and symbolic-link targets.
- A mocked metadata `OSError` producing a printed warning while scanning continues with other valid files.
- A separate implementation-level check that enumeration stops after observing `limit + 1` entries when the limit is exceeded.

These tests establish the checked behavior for the fixtures used. They do not prove complete filesystem security, resistance to races, or compatibility with every filesystem.

### Verified results

| Environment                 | Python          | Tests | Failures | Errors | Skips | Result |
| --------------------------- | --------------- | ----- | -------- | ------ | ----- | ------ |
| Local macOS                 | 3.14.4          | 22    | 0        | 0      | 0     | Passed |
| GitHub Actions macOS runner | CPython 3.14.10 | 22    | 0        | 0      | 0     | Passed |

The scanner tests, CI workflow, and testing documentation were merged into `main` through [pull request #1](https://github.com/yaryary/local-file-organizer/pull/1). After syncing the merged changes, all 22 tests passed again locally with no failures, errors, or skipped tests.

### Continuous integration

The workflow in `.github/workflows/scanner-tests.yml` is configured to run on pushes and pull requests and includes a manual-dispatch trigger. It uses a `macos-latest` runner, Python 3.14, read-only repository contents permissions, and a five-minute job timeout.

The workflow checks out the repository, sets up Python, and runs:

```bash
python -m unittest discover -s tests -v
```

It does not install Ollama, download models, start the agent, or upload scan inventories.

Failure detection was verified on the test branch: an intentionally incorrect assertion caused the workflow to fail with one test failure and exit code 1. Restoring the correct assertion returned CI to a passing state.

[Verified passing pull-request CI run](https://github.com/yaryary/local-file-organizer/actions/runs/41304282532)

## Not yet tested

- Request timeout behavior.
- Invalid JSON returned by the server.
- Empty or otherwise unusable response content.
- Automated tests for the Ollama connection and response-handling code.
- Scanner compatibility with older Python versions and non-macOS runners.

## Planned architecture

```text
Selected test folder
        |
        v
Read-only scanner and bounded content previews
        |
        v
Local model proposes categories and names
        |
        v
Python validates paths, names, limits, and collisions
        |
        v
Dry-run preview and explicit approval
        |
        v
Approved operations and a recovery manifest
```

The read-only scanner is implemented. Content previews, model-driven classification, path validation for proposed changes, dry-run approval, execution, and recovery records remain planned. The model will propose changes, while Python will enforce filesystem rules and control execution.

## Roadmap

| Milestone | Scope                                                  | Status                                                                          |
| --------- | ------------------------------------------------------ | ------------------------------------------------------------------------------- |
| M0        | Local model connection and useful failure messages     | Core manual connection tests passed; setup documented here                      |
| M1        | Read-only scanner and metadata collection              | Implemented; manual tests and 22 automated tests passed locally and in macOS CI |
| M2        | Bounded content previews and structured classification | Planned                                                                         |
| M3        | Validated dry-run plans                                | Planned                                                                         |
| M4        | Approved execution and recovery records                | Planned                                                                         |
| M5        | Bounded tool-calling agent loop                        | Planned                                                                         |
| M6        | Evaluation, documentation, and portfolio release       | Planned                                                                         |

### Next steps

- Connect the read-only scanner to the application without adding file modification behavior.
- Add bounded file-content previews with explicit limits on file size and extracted text.
- Use metadata and previews to develop structured, local-model classification.
- Add tests for new preview and classification behavior as those features are implemented.

## Safety and privacy goals

The organizer will be developed against disposable, synthetic files before use with personal folders. Planned safeguards include:

- Explicit input and output boundaries.
- Read-only scanning before any mutation features.
- Bounded file previews and scan limits.
- Rejection of unsafe paths and symbolic links under the initial policy.
- No silent overwrites or deletions.
- A dry-run preview and approval tied to the exact proposed plan.
- Per-operation results and a recovery manifest.
- Treating file contents and model responses as untrusted data.

Recovery will be best effort, not a replacement for backups. Keep personal files, real-content fixtures, and private logs out of version control.
