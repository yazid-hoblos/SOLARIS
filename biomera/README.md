# BIOMERA — the Solaris Chatbot Agent

BIOMERA is a chatbot-style AI agent that runs and orchestrates SOLARIS commands. The public chatbot is available at:

https://solaris-chatbot-wwd4.onrender.com/

![alt text](figures/biomera-gui.png)

Use the chatbot to interact with SOLARIS modules (pathway profiler, pangenomic analyzer, compatibility predictor) using natural language. BIOMERA converts user instructions into planned steps and safely executes Solaris commands inside controlled environments.

This README explains what BIOMERA is, how the repository is organized, how the system works, and how to run it locally or in Docker/Render.

## High level: how BIOMERA works
- Input: a user message (chat) describing a task.
- Planner: an LLM (local via Ollama or remote via API) parses the request and generates an action plan.
- Validator & Safety: commands are validated (required flags, disallowed interactive prompts). The agent will refuse unsafe or interactive execution unless explicitly permitted.
- Executor: validated commands are run inside a controlled executor (local sandbox or Docker executor). Output, logs and any files created are returned to the user.

Key design goals: safety (no hidden interactive prompts), reproducibility (Docker), and explainability (the agent returns both an apology/explanation and the raw terminal output when commands fail).

## Repository structure

The `biomera/` folder contains the chatbot agent, web UI assets and supporting runtime directories. Current layout (folders and notable files):

- `api.py` — Flask-based HTTP API used by the web UI.
- `cli.py` — command-line entrypoint to start the agent interactively.
- `main.py` — main chat/agent orchestration loop used in CLI mode.
- `Dockerfile` — Docker image definition for production/Render builds.
- `start_gui.sh` and `GUI_README.md` — helper script and notes to start the optional GUI.
- `bioprod.log` — runtime log file (generated at runtime).
- `requirements.txt` — Python dependencies for the BIOMERA service.

- `config/` — configuration files for the agent (LLM settings, prompts, tool definitions).
- `model/` — LLM adapter / model integration code used by BIOMERA.
- `sandbox/` — sandboxed execution helpers and safety wrappers used when running commands.
- `utils/` — BIOMERA helper utilities (small scripts used by the agent and API).

- `public/` — static web assets (HTML/CSS/JS) for the web UI.
- `workspace/` — agent workspace (user session files, generated artifacts).

This README documents the BIOMERA components; if you expect additional files or a different layout please tell me and I will adjust the documentation accordingly.


## How to run

### 1) Quick local (development)

Run inside a Python virtualenv and use the Python entrypoint (development mode):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt

# start the chat agent (interactive terminal)
python biomera/start_gui.sh
```

Configuration:
- Edit `config/config.json` to select `use_online` or local Ollama model. Set API keys via environment variables for online models.

### 2) Docker (recommended / production)

```bash
# build the image
docker build -f biomera/Dockerfile -t solaris-biomera:dev .

# run the container and connect to the chat service
docker run --rm -it -p 5000:5000 solaris-biomera:dev
```
