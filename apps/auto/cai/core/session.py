"""
apps/auto/cai/core/session.py

管理交互式會話和命令執行的核心邏輯。
從 CAI 移植並簡化。
"""

import os
import pty
import select
import signal
import subprocess
import threading
import time
import uuid
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ACTIVE_SESSIONS: Dict[str, 'ShellSession'] = {}

class ShellSession:
    """使用 PTY 管理交互式 Shell 會話。"""
    
    def __init__(self, command: str, cwd: Optional[str] = None):
        self.session_id = str(uuid.uuid4())[:8]
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.process = None
        self.master = None
        self.slave = None
        self.output_buffer: List[str] = []
        self.is_running = False
        self.last_activity = time.time()

    def start(self):
        """在虛擬終端中啟動進程。"""
        try:
            self.master, self.slave = pty.openpty()
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdin=self.slave,
                stdout=self.slave,
                stderr=self.slave,
                cwd=self.cwd,
                preexec_fn=os.setsid,
                universal_newlines=True,
            )
            self.is_running = True
            logger.info(f"Started session {self.session_id}: {self.command}")
            threading.Thread(target=self._read_output, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start session {self.session_id}: {e}")
            self.is_running = False

    def _read_output(self):
        """線程化的輸出讀取器。"""
        try:
            while self.is_running and self.master:
                if self.process.poll() is not None:
                    self.is_running = False
                    break
                
                # 非阻塞讀取
                ready, _, _ = select.select([self.master], [], [], 0.5)
                if ready:
                    try:
                        data = os.read(self.master, 4096).decode('utf-8', errors='replace')
                        if data:
                            self.output_buffer.append(data)
                            self.last_activity = time.time()
                        else:
                            self.is_running = False
                            break
                    except OSError:
                        self.is_running = False
                        break
        except Exception as e:
            logger.error(f"讀取會話 {self.session_id} 時出錯: {e}")
            self.is_running = False

    def send_input(self, input_data: str):
        """發送標準輸入到進程。"""
        if not self.is_running or not self.master:
            return "會話未執行"
        try:
            os.write(self.master, (input_data + "\n").encode())
            return "輸入已發送"
        except Exception as e:
            return f"錯誤: {e}"

    def get_output(self, clear: bool = True) -> str:
        """獲取輸出緩衝區內容。"""
        output = "".join(self.output_buffer)
        if clear:
            self.output_buffer = []
        return output

    def terminate(self):
        """殺死進程組。"""
        if not self.process:
            return
        self.is_running = False
        try:
            pgid = os.getpgid(self.process.pid)
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(0.5)
            if self.process.poll() is None:
                os.killpg(pgid, signal.SIGKILL)
        except Exception:
            pass
        finally:
            if self.master:
                try: os.close(self.master)
                except: pass
                self.master = None
            if self.slave:
                try: os.close(self.slave)
                except: pass
                self.slave = None

def run_command(command: str, cwd: Optional[str] = None, timeout: int = 60) -> str:
    """執行一次性命令並返回合併後的輸出。"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        return f"超時: {e.stdout}{e.stderr}"
    except Exception as e:
        return f"錯誤: {str(e)}"
