import logging
import shlex
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)

# 系統唯讀目錄：bwrap 需要綁定這些才能讓 Kali 工具正常運作
_RO_BINDS = [
    "/usr", "/lib", "/lib64", "/bin", "/sbin",
    "/etc", "/etc/resolv.conf",
]
# /scripthub 是 skill 腳本的共用目錄，需要跨 target 共用（唯讀）
_SHARED_RO = ["/scripthub"]


class SandboxMixin:
    """
    Sandbox Execution Tools Mixin.
    每個 target 都有獨立的 workspace（/workspace/target_<id>），
    透過 bwrap 建立命名空間隔離，防止跨 target 讀寫。
    """

    def _resolve_target_id(self, overview_id: int) -> int | None:
        """從 Overview ID 解析出 Target ID。"""
        if not overview_id:
            return None
        try:
            from apps.core.models import Overview
            ov = Overview.objects.filter(id=overview_id).only("target_id").first()
            return ov.target_id if ov else None
        except Exception as e:
            logger.warning(f"[_resolve_target_id] overview_id={overview_id}: {e}")
            return None

    def _ensure_workspace(self, target_id: int) -> str | None:
        """在 sandbox 內確保 /workspace/target_<id> 存在，回傳絕對路徑。

        Returns:
            workspace 絕對路徑，或 None（container 不可用時）。
        """
        if not target_id:
            return None
        import docker
        workspace = f"/workspace/target_{target_id}"
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            exit_code, _ = container.exec_run(
                cmd=["/bin/bash", "-c", f"mkdir -p {workspace} && chmod 700 {workspace}"],
                detach=False,
                stream=False,
            )
            if exit_code != 0:
                logger.error(f"[_ensure_workspace] mkdir failed for {workspace}")
                return None
            return workspace
        except Exception as e:
            logger.error(f"[_ensure_workspace] {e}")
            return None

    def _build_bwrap_args(self, workspace: str) -> list[str]:
        """建構 bwrap 的參數列表。

        策略：
        - workspace 唯一可寫目錄（bind）
        - 系統工具目錄唯讀（ro-bind）
        - /scripthub 共用唯讀（skill 腳本）
        - /dev /proc /tmp 標準配置
        - HOME 指向 workspace
        """
        args: list[str] = ["bwrap", "--die-with-parent"]
        # 唯一可寫的家目錄
        args += ["--bind", workspace, workspace]
        # 系統工具唯讀
        for ro in _RO_BINDS:
            args += ["--ro-bind", ro, ro]
        # 共用的 skill 腳本目錄（唯讀）
        for ro in _SHARED_RO:
            args += ["--ro-bind", ro, ro]
        # 標準虛擬檔案系統
        args += ["--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
        # 清掉可能指向不存在路徑的 HOME（bash 會抱怨）
        args += ["--unsetenv", "HOME", "--setenv", "HOME", workspace]
        return args

    def _wrap_command(self, command: str, workspace: str | None) -> str:
        """把原始指令用 bwrap 包裝。如果 workspace=None 就直接回傳原指令。"""
        if not workspace:
            return command
        bwrap_args = self._build_bwrap_args(workspace)
        # 用 shlex.quote 確保 command 作為單一字串傳給 bash -c
        wrapped = " ".join(shlex.quote(a) for a in bwrap_args)
        wrapped += " /bin/bash -c " + shlex.quote(command)
        return wrapped

    @method_tool
    def run_command(self, command: str, overview_id: int = None) -> str:
        """
        Run shell commands in a completely isolated Kali Linux Sandbox.
        每個 target 有獨立的 workspace（/workspace/target_<id>），
        透過 bwrap 命名空間隔離，無法跨 target 讀寫檔案。

        Use this as a fallback if API scanners fail, or to curl/interact
        with pages natively. pip install 不需要額外參數（環境已配置）。

        Args:
            command: 要執行的 shell 指令。
            overview_id: (Auto-injected) 當前 Overview ID，用來解析 workspace。
        """
        import docker
        try:
            # 解析 target_id 並確保 workspace 存在
            target_id = self._resolve_target_id(overview_id)
            workspace = self._ensure_workspace(target_id) if target_id else None

            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "sandbox_command_started",
                    status="started",
                    content=command,
                    payload={
                        "command": command,
                        "target_id": target_id,
                        "workspace": workspace,
                    },
                    tool_name="run_command",
                )

            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            wrapped_cmd = self._wrap_command(command, workspace)

            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", wrapped_cmd],
                detach=False,
                stream=False,
            )

            res = f"Execution Environment: Kali Docker Sandbox"
            if workspace:
                res += f" (isolated workspace: {workspace})"
            res += f"\nExit Code: {exit_code}\n"
            res += f"Output:\n{output_bytes.decode('utf-8', errors='replace')}"

            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "sandbox_command_finished",
                    status="success" if exit_code == 0 else "failed",
                    content=f"Exit Code: {exit_code}",
                    payload={
                        "command": command,
                        "exit_code": exit_code,
                        "workspace": workspace,
                    },
                    tool_name="run_command",
                )
            return res
        except docker.errors.NotFound:
            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "sandbox_command_error",
                    status="failed",
                    content="Sandbox container c2_kali_sandbox not found",
                    payload={"command": command, "error_type": "NotFound"},
                    tool_name="run_command",
                )
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請先透過 docker compose up -d 啟動。"
        except Exception as e:
            if hasattr(self, "emit_thread_event"):
                self.emit_thread_event(
                    "sandbox_command_error",
                    status="failed",
                    content=str(e),
                    payload={"command": command, "error_type": type(e).__name__},
                    tool_name="run_command",
                )
            return f"Sandbox Command Failed: {e}"
