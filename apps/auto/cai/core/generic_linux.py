"""
apps/auto/cai/core/generic_linux.py

使用原生會話管理實現的 generic_linux_command 工具。
"""

import logging
from typing import Optional
from .tool import function_tool
from .session import run_command, ShellSession, ACTIVE_SESSIONS

logger = logging.getLogger(__name__)

@function_tool
def generic_linux_command(command: str, interactive: bool = False, session_id: Optional[str] = None) -> str:
    """
    執行 Linux 命令。支持交互式會話。
    
    參數:
        command: 要執行的命令。
        interactive: 是否啟動交互式會話。
        session_id: 現有會話的 ID，用於發送輸入。
        
    返回:
        命令輸出或會話狀態。
    """
    if session_id:
        if session_id in ACTIVE_SESSIONS:
            session = ACTIVE_SESSIONS[session_id]
            if command.strip().lower() == "exit":
                session.terminate()
                del ACTIVE_SESSIONS[session_id]
                return f"會話 {session_id} 已終止。"
            session.send_input(command)
            # 給予一點時間產生輸出
            import time
            time.sleep(0.5)
            return session.get_output()
        else:
            return f"錯誤: 找不到會話 {session_id}。"

    if interactive:
        session = ShellSession(command)
        session.start()
        ACTIVE_SESSIONS[session.session_id] = session
        # 等待初始輸出
        import time
        time.sleep(1)
        output = session.get_output()
        return f"會話 {session.session_id} 已啟動。輸出：\n{output}"

    # 默認：一次性命令
    return run_command(command)
