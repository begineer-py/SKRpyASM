import logging
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class SandboxMixin:
    """
    Sandbox Execution Tools Mixin
    Provides tools for running commands in an isolated Kali Linux sandbox environment.
    """

    @method_tool
    def run_command(self, command: str) -> str:
        """
        Run shell commands in a completely isolated Kali Linux Sandbox.
        Use this as a fallback if API scanners fail, or to curl/interact with pages natively during Phase B.
        The executed commands will run securely via Docker.
        """
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", command],
                detach=False,
                stream=False
            )
            
            res = f"Execution Environment: Kali Docker Sandbox\n"
            res += f"Exit Code: {exit_code}\n"
            res += f"Output:\n{output_bytes.decode('utf-8', errors='replace')}"
            return res
        except docker.errors.NotFound:
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請先透過 start_sandbox.sh 啟動。"
        except Exception as e:
            return f"Sandbox Command Failed: {e}"
