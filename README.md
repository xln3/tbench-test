# tbench-test

PANDA agent adapter for [Terminal-Bench](https://github.com/terminal-bench/terminal-bench) evaluation. Runs the pre-compiled PANDA binary inside Terminal-Bench task containers.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PANDA_API_KEY` / `OPENAI_API_KEY` | Yes | LLM API key |
| `PANDA_BASE_URL` / `OPENAI_BASE_URL` | Yes | LLM API endpoint |
| `PANDA_MODEL` | Yes | Model name (or pass `--model`) |
| `PANDA_PROVIDER` | No | Provider type (default: `openai`) |
| `PANDA_MAX_TOKENS` | No | Max output tokens (default: `32768`) |
| `PANDA_THINKING` | No | Enable thinking mode (default: `true`) |
| `PANDA_THINKING_BUDGET` | No | Thinking token budget |

## Usage

The PANDA binary must be pre-compiled and placed at `/tmp/panda-bin` before running:

```bash
# Build PANDA binary (from the PANDA project)
deno compile --allow-all --output /tmp/panda-bin mod.ts

# Run Terminal-Bench with PANDA agent
terminal-bench run --agent panda --tasks <task_ids>
```

## Files

- `panda_agent.py` — Agent adapter that copies the PANDA binary into task containers and executes it
- `panda-setup.sh` — Alternative setup script for installing Deno inside containers (not used by the binary approach)
- `runs/` — Evaluation run logs and results

## Run History

`runs/` contains timestamped evaluation runs. Each run directory includes per-task results, agent transcripts, and terminal session logs.
