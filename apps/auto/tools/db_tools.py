"""
Database Tools for Auto Agent
This module provides a unified interface to database manipulation tools by composing multiple domain-specific mixins.
"""
import logging
from apps.auto.tools.reconnaissance_tools import ReconnaissanceMixin
from apps.auto.tools.asset_creation_tools import AssetCreationMixin
from apps.auto.tools.endpoint_tools import EndpointMixin
from apps.auto.tools.memory_tools import MemoryMixin
from apps.auto.tools.skill_tools import SkillMixin
from apps.auto.tools.sandbox_tools import SandboxMixin
from apps.auto.tools.step_management_tools import StepManagementMixin
from apps.auto.tools.cve_intelligence_tools import CVEIntelligenceMixin

logger = logging.getLogger(__name__)


class DBToolsMixin(
    ReconnaissanceMixin,
    AssetCreationMixin,
    EndpointMixin,
    MemoryMixin,
    SkillMixin,
    SandboxMixin,
    StepManagementMixin,
    CVEIntelligenceMixin,
):
    """
    統一的資料庫工具 Mixin，提供給 Auto Agent 呼叫的資料庫操縱工具。
    所有繼承自此 Mixin 的 Assistant 皆會繼承這些 @method_tool。

    本 Mixin 由以下領域特定的 Mixin 組成：
    - ReconnaissanceMixin: 偵察與上下文查詢工具
    - AssetCreationMixin: 資產登記工具
    - EndpointMixin: API 端點智能工具
    - MemoryMixin: 長期記憶與內容壓縮
    - SkillMixin: 技能系統管理
    - SandboxMixin: 沙箱命令執行
    - StepManagementMixin: 步驟管理與工作流程
    - CVEIntelligenceMixin: CVE 情報查詢與豐富化
    """
    pass
