# IOMP - Talk2Shell

Talk2Shell is a local command assistant that turns natural language into system commands, checks them for safety, and can execute them in a controlled way.

The current implementation has a launcher-first experience:

- PowerShell is supported as the primary shell target.
- Bash is supported for local development and non-Windows environments.
- Terminal launcher is the default launch mode.
- Web UI is available as an optional online mode.
- Terminal mode executes by default unless dry-run is turned on.
- Risky commands require confirmation or are blocked.
- Risky and multi-step tasks can be queued for approval before execution.
- Administrator relaunch is available on Windows from the launcher.
- Native Windows terminal launch is available from VS Code with `--native-window`.
- Optional AI translation is supported when `OPENAI_API_KEY` is set.
- Windows launch scripts are included in `launch.cmd` and `launch.ps1`.

## What It Does

- Translate short English instructions into shell commands.
- Handle simple multi-step requests.
- Flag destructive or sensitive commands before execution.
- Show the generated command, safety analysis, and execution output in a browser UI.

## Project Structure


```text
IOMP/
├── app/
│   ├── core/
│   │   ├── executor.py
│   │   ├── models.py
│   │   ├── safety.py
│   │   ├── service.py
│   │   └── translator.py
│   ├── main.py
│   └── web/
│       ├── static/
│       │   ├── app.js
│       │   └── styles.css
│       └── templates/
│           └── index.html
├── main.py
├── requirements.txt
└── tests/
```

## Architecture

1. Input handler receives a natural-language instruction from the browser UI.
2. Translator converts the instruction into one or more shell commands.
3. Safety checker inspects the commands for destructive or sensitive patterns.
4. Executor runs the command only when the request is allowed and execution is enabled.
5. Output handler returns the translation, safety result, and execution output to the UI.

When a task needs manual review, the backend creates an approval request with step-level detail instead of executing immediately.

## Supported Examples

- `create a folder named reports`
- `delete all txt files`
- `list processes`
- `create a folder named test and then list files`
- `change directory to downloads`
- `show system info`
- `stop process notepad`

## Automation Section

Automation requests are handled separately from direct shell commands.

- System setup automation covers tasks like installing Python, creating a virtual environment, and installing dependencies.
- Browser automation covers tasks like opening WhatsApp Web and preparing a message workflow.
- Browser automation plans now execute as a browser-launch preview with explicit manual follow-up steps when a full browser runner is not available.
- The launcher shows automation as its own section so it stays distinct from normal command translation.

## Installation

1. Create or activate the Python environment for the repository.
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Start the launcher:

```bash
python main.py
```

4. Start terminal mode directly:

```bash
python main.py --terminal
```

5. To start the web UI instead:

```bash
python main.py --web
```

6. Open the browser at `http://127.0.0.1:8000` only when using `--web`.

7. On Windows, double-click `launch.cmd` or run `launch.ps1` to open the native launcher.

## Launcher Flow

When you start the app normally, you will see:

1. Stay offline
2. Go online
3. Exit

Inside offline mode, you can choose:

1. Continue with terminal
2. Continue as administrator
3. Open a native Windows terminal
4. Back

Inside online mode, you can choose:

1. Start web UI
2. Open web view in browser
3. Back

## Terminal UX

The terminal interface is designed to keep the user focused on natural language, not code:

- It shows a short banner, current mode, and quick controls.
- It summarizes the understood instruction in plain language.
- It shows safety status as a simple pass/block/confirm result.
- It shows execution status and output without exposing backend details by default.
- A `:details on` command is available if you want deeper output while debugging.

## Usage

The app defaults to dry-run mode, so it will show the generated commands without executing them.

If you want to run a command locally:

1. Turn off dry-run.
2. Confirm risky commands if prompted.
3. Make sure the selected shell exists on the current machine.

## Safety Model

The safety layer blocks or flags commands that look destructive, such as:

- recursive deletion
- registry edits
- system shutdown or disk tooling
- commands that target sensitive system paths

The implementation intentionally prefers caution over execution.

## API Endpoints

- `POST /api/analyze` returns translation and safety results.
- `POST /api/run` analyzes, checks safety, and optionally executes the command.
- `GET /api/history` returns recent activity from the current process.
- `POST /api/feedback` records successful instruction-to-command mappings.
- `GET /api/learned` lists learned mappings, optionally by shell.
- `GET /api/audit` returns recent audit events.
- `GET /api/approvals` lists approval requests.
- `GET /api/approvals/{id}` returns a single approval request.
- `POST /api/approvals/{id}/approve` approves all or selected steps, optionally executing after approval.
- `POST /api/approvals/{id}/deny` denies a queued request.

## AI Mode

If you set `OPENAI_API_KEY`, the translator can use an LLM to map natural language into shell commands when rules do not match.

If no key is set, the rule-based translator and direct command passthrough still work.

## Learning Loop

The backend can learn from successful tasks:

- Successful non-dry-run commands are recorded and reused for similar future instructions.
- You can provide manual success feedback through the API.
- Learned mappings are queryable through the API.

## Execution Profiles

The backend supports execution profiles to control automation strictness:

- `safe` prioritizes manual approval.
- `balanced` uses the default policy.
- `power_user` reduces friction for trusted local workflows while still blocking dangerous commands.

## Approval Queue

Approval requests are persisted when a command or automation plan needs review.

- Each request stores the instruction, shell, profile, safety summary, commands, and step-by-step review state.
- Multi-step plans expose individual steps so you can approve them incrementally.
- Approved requests can be executed afterward through the API, or left as reviewed records.

## Testing

Run the test suite with:

```bash
pytest
```

## Notes

- PowerShell is the default shell target.
- Bash is included so the project remains usable on this Linux workspace.
- The translator is rule-based and intentionally simple. It is designed as a solid starting point for a more advanced NLP layer later.
