"""
PANDA agent adapter for Terminal-Bench.

Copies a pre-compiled PANDA binary into the task container and runs it with --prompt.
No Deno installation or dependency download required inside the container.
"""

import io
import os
import shlex
import tarfile
from pathlib import Path

from terminal_bench.agents.base_agent import AgentResult, BaseAgent
from terminal_bench.agents.failure_mode import FailureMode
from terminal_bench.terminal.models import TerminalCommand
from terminal_bench.terminal.tmux_session import TmuxSession

# Pre-compiled PANDA binary (built with `deno compile --allow-all`)
PANDA_BINARY = Path("/tmp/panda-bin")


def _create_binary_tar() -> io.BytesIO:
    """Create a tar archive containing the PANDA binary."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        tar.add(str(PANDA_BINARY), arcname="panda")
    buf.seek(0)
    return buf


class PandaAgent(BaseAgent):
    """PANDA agent for Terminal-Bench evaluation."""

    def __init__(self, model_name: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._model_name = model_name

    @staticmethod
    def name() -> str:
        return "panda"

    def _get_env_vars(self) -> dict[str, str]:
        """Collect env vars for PANDA from host environment."""
        env = {}

        # API config
        for key in ("PANDA_API_KEY", "OPENAI_API_KEY"):
            if key in os.environ:
                env["PANDA_API_KEY"] = os.environ[key]
                break
        if "PANDA_API_KEY" not in env:
            raise ValueError(
                "PANDA_API_KEY or OPENAI_API_KEY must be set in the environment"
            )

        for key in ("PANDA_BASE_URL", "OPENAI_BASE_URL"):
            if key in os.environ:
                env["PANDA_BASE_URL"] = os.environ[key]
                break
        if "PANDA_BASE_URL" not in env:
            raise ValueError("PANDA_BASE_URL or OPENAI_BASE_URL must be set")

        if self._model_name:
            env["PANDA_MODEL"] = self._model_name
        elif "PANDA_MODEL" in os.environ:
            env["PANDA_MODEL"] = os.environ["PANDA_MODEL"]
        else:
            raise ValueError("PANDA_MODEL must be set or --model must be provided")

        env["PANDA_PROVIDER"] = os.environ.get("PANDA_PROVIDER", "openai")
        env["PANDA_MAX_TOKENS"] = os.environ.get("PANDA_MAX_TOKENS", "32768")
        env["PANDA_THINKING"] = os.environ.get("PANDA_THINKING", "true")

        budget = os.environ.get("PANDA_THINKING_BUDGET")
        if budget:
            env["PANDA_THINKING_BUDGET"] = budget

        return env

    def perform_task(
        self,
        instruction: str,
        session: TmuxSession,
        logging_dir: Path | None = None,
    ) -> AgentResult:
        container = session.container

        # 1. Copy pre-compiled binary to /usr/local/bin/panda
        binary_tar = _create_binary_tar()
        container.put_archive("/usr/local/bin", binary_tar.read())
        binary_tar.close()
        container.exec_run(["chmod", "+x", "/usr/local/bin/panda"])

        # 2. Set env vars (outside tmux to hide secrets)
        env_vars = self._get_env_vars()
        env_lines = "\n".join(f"export {k}='{v}'" for k, v in env_vars.items())
        container.exec_run(
            ["sh", "-c", f"mkdir -p /installed-agent && echo {shlex.quote(env_lines)} > /installed-agent/setup-env.sh"]
        )

        session.send_keys(
            ["source /installed-agent/setup-env.sh", "Enter"],
            block=True,
            max_timeout_sec=float("inf"),
        )

        # 3. Run PANDA with the task instruction
        rendered = self._render_instruction(instruction)
        escaped = shlex.quote(rendered)
        cmd = f"panda --prompt {escaped}"

        session.send_command(
            TerminalCommand(
                command=cmd,
                max_timeout_sec=float("inf"),
                block=True,
            )
        )

        return AgentResult()
