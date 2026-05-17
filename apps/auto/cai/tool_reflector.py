"""
Tool Reflector for AutomationAgent

自動掃描 AutomationAgent 的所有工具 (DBTools, ScannerTools, API Tools)，
並生成結構化的工具詳情和文檔，用於動態注入到系統提示詞中。
"""

import inspect
import logging
import re
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolReflector:
    """
    自動反射 AutomationAgent 的工具配置，提供結構化的工具詳情。
    採用靜態代碼分析方法，避免運行時依賴。
    """
    
    def __init__(self):
        """初始化反射器"""
        self._cache = {}
    
    def reflect_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        反射所有工具，並按類別分組。
        
        Returns:
            {
                'db_tools': [...],
                'scanner_tools': [...],
                'api_tools': [...]
            }
        """
        if 'reflected' in self._cache:
            return self._cache['reflected']
        
        result = {
            'db_tools': self._extract_db_tools(),
            'scanner_tools': self._extract_scanner_tools(),
            'api_tools': self._extract_api_tools()
        }
        
        self._cache['reflected'] = result
        return result
    
    def _extract_db_tools(self) -> List[Dict[str, Any]]:
        """
        通過靜態代碼分析提取 DBTools。
        """
        tools = []
        try:
            db_tools_path = Path(__file__).parent.parent / "tools" / "db_tools.py"
            tools = self._parse_tools_from_file(str(db_tools_path), "DBTools")
        except Exception as e:
            logger.warning(f"Failed to extract DB tools: {e}")
        return tools
    
    def _extract_scanner_tools(self) -> List[Dict[str, Any]]:
        """
        通過靜態代碼分析提取 ScannerTools。
        """
        tools = []
        try:
            scanner_tools_path = Path(__file__).parent.parent / "tools" / "scanner_tools.py"
            tools = self._parse_tools_from_file(str(scanner_tools_path), "ScannerTools")
        except Exception as e:
            logger.warning(f"Failed to extract Scanner tools: {e}")
        return tools
    
    def _extract_api_tools(self) -> List[Dict[str, Any]]:
        """
        API 工具由運行時動態生成，這裡返回提示信息。
        """
        return [
            {
                'name': 'API Tools (Dynamic)',
                'category': 'APITools',
                'description': 'Dynamic tools generated from OpenAPI schema for platform-specific operations',
                'parameters': [],
                'full_doc': 'These tools are generated at runtime from the OpenAPI schema'
            }
        ]
    
    def _parse_tools_from_file(self, file_path: str, category: str) -> List[Dict[str, Any]]:
        """
        從 Python 文件中靜態提取 @method_tool 修飾的方法。
        
        Args:
            file_path: Python 文件路徑
            category: 工具類別 ('DBTools' or 'ScannerTools')
        
        Returns:
            工具列表
        """
        tools = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 正則表達式提取 @method_tool 修飾的方法
            # 匹配模式：@method_tool\n    def method_name(...) -> return_type:\n        """docstring"""
            pattern = r'@method_tool\s+def\s+(\w+)\s*\((.*?)\)\s*->\s*\w+:\s+"""(.*?)"""'
            
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                method_name = match.group(1)
                params_str = match.group(2)
                docstring = match.group(3)
                
                # 解析參數
                params = []
                if params_str:
                    # 移除 self 參數
                    param_list = [p.strip() for p in params_str.split(',') if p.strip()]
                    params = [p.split(':')[0].strip() for p in param_list if p and p.strip() != 'self']
                
                # 提取第一行作為簡短描述
                first_line = docstring.strip().split('\n')[0].strip()
                
                tools.append({
                    'name': method_name,
                    'category': category,
                    'description': first_line or f"{category} tool: {method_name}",
                    'parameters': params,
                    'full_doc': docstring.strip()
                })
        
        except Exception as e:
            logger.warning(f"Failed to parse tools from {file_path}: {e}")
        
        return tools
    
    def generate_tool_markdown(self) -> str:
        """
        生成 Markdown 格式的工具文檔，用於注入到系統提示詞。
        
        Returns:
            格式化的 Markdown 文本
        """
        tools = self.reflect_tools()
        
        lines = []
        lines.append("## AVAILABLE TOOLS CATALOG\n")
        lines.append("AutomationAgent (Layer 3) has access to 40+ tools organized into three categories:\n")
        
        # Database Tools
        db_count = len(tools['db_tools'])
        lines.append(f"\n### 📊 DBTools (Database & Data Management) - {db_count} tools")
        lines.append("These tools interact with the database for reconnaissance, planning, and knowledge management.\n")
        
        if tools['db_tools']:
            for tool in sorted(tools['db_tools'], key=lambda x: x['name']):
                params_str = f"({', '.join(tool['parameters'])})" if tool['parameters'] else "()"
                lines.append(f"- **{tool['name']}{params_str}** - {tool['description']}")
        
        # Scanner Tools
        scanner_count = len(tools['scanner_tools'])
        lines.append(f"\n### 🔍 ScannerTools (Penetration Testing Scanners) - {scanner_count} tools")
        lines.append("These tools execute reconnaissance and vulnerability scanning operations.\n")
        
        if tools['scanner_tools']:
            for tool in sorted(tools['scanner_tools'], key=lambda x: x['name']):
                params_str = f"({', '.join(tool['parameters'])})" if tool['parameters'] else "()"
                lines.append(f"- **{tool['name']}{params_str}** - {tool['description']}")
        
        # API Tools
        lines.append("\n### 🌐 APITools (Platform API Endpoints)")
        lines.append("Dynamic tools generated from OpenAPI schema for platform-specific operations at runtime.\n")
        
        return "\n".join(lines)
    
    def generate_tool_decision_tree(self) -> str:
        """
        生成工具決策樹文檔，幫助 Layer 2 選擇合適工具。
        """
        lines = []
        lines.append("\n## TOOL SELECTION GUIDE (How to Choose Tools)\n")
        
        lines.append("### When to Use DBTools:")
        lines.append("- **get_target_context(target_name)** - ALWAYS call this first before any operation")
        lines.append("- **create_overview(target_id, ...)** - Create a new Overview if none exists for target")
        lines.append("- **get_url_intelligence(url_id)** - Query comprehensive data about a specific URL")
        lines.append("- **write_recon_note(overview_id, ...)** - Save discoveries and observations")
        lines.append("- **update_overview_status(overview_id, ...)** - Update plan, risk_score, knowledge after findings")
        lines.append("- **check_scanned_urls() / check_scanned_subdomains() / check_scanned_ips()** - Query existing scan status")
        lines.append("- **run_command() / execute_skill_script()** - Execute custom scripts in sandbox")
        lines.append("- **search_skills() / load_skill()** - Reuse existing scripts for complex tasks\n")
        
        lines.append("### When to Use ScannerTools:")
        lines.append("- **run_flaresolverr_crawler()** - Fetch website content, extract URLs and Forms")
        lines.append("- **run_subfinder_discovery()** - Enumerate subdomains passively")
        lines.append("- **run_gau_url_discovery()** - Collect historical URLs from passive sources")
        lines.append("- **run_nmap_port_scan()** - Full TCP port scan on target IPs")
        lines.append("- **run_nuclei_tech_scan_*()** - Detect technology stack (last resort, prefer Kali tools)")
        lines.append("- **run_nuclei_vuln_scan_*()** - Scan for known vulnerabilities (last resort, prefer Kali tools)\n")
        lines.append("\n### Prefer Kali Linux Native Tools (via `run_command`):")
        lines.append("The sandbox is a Kali Linux container. Use these instead of Nuclei when possible:")
        lines.append("- **Directory busting**: `gobuster dir -u <url> -w /usr/share/wordlists/dirb/common.txt`")
        lines.append("- **SQL injection**: `sqlmap -u <url> --batch --random-agent`")
        lines.append("- **Brute-force**: `hydra -l admin -P /usr/share/wordlists/rockyou.txt <target> <service>`")
        lines.append("- **Web vuln scan**: `nikto -h <url>`")
        lines.append("- **Fuzzing**: `wfuzz -c -z file,/usr/share/wordlists/wfuzz/general/common.txt <url>/FUZZ`\n")
        
        lines.append("### CRITICAL Workflow Rules:")
        lines.append("1. **ALWAYS** call `get_target_context(target_name)` first to get valid IDs")
        lines.append("2. Use `check_scanned_*()` tools BEFORE running expensive scanners to avoid redundant work")
        lines.append("3. Call `get_url_intelligence()` to understand page content BEFORE running vulnerability scanners")
        lines.append("4. Record findings with `write_recon_note()` IMMEDIATELY after each action")
        lines.append("5. Never guess or invent IDs - ONLY use IDs returned by database tools\n")
        
        return "\n".join(lines)


def get_tool_reflector() -> ToolReflector:
    """
    全局 Tool Reflector 實例。
    """
    global _reflector
    if '_reflector' not in globals():
        _reflector = ToolReflector()
    return _reflector
