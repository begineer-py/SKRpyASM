import logging
from django_ai_assistant import method_tool
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class DBToolsMixin:
    """
    提供給 Auto Agent 呼叫的資料庫操縱工具 Mixin。
    所有繼承自此 Mixin 的 Assistant 皆會繼承這些 @method_tool。
    """

    @method_tool
    def update_overview_status(self, overview_id: int, new_knowledge: dict = None, new_plan: dict = None) -> str:
        """
        更新目標 Overview（專案概覽）的 knowledge (威脅情報與知識) 與 plan (接下來的攻擊藍圖)。
        確保知識庫隨時保持最新。
        
        Args:
            overview_id: The ID of the Overview.
            new_knowledge: A JSON dictionary representing discovered intelligence.
            new_plan: A JSON dictionary outlining the strategic attack plan.
        """
        try:
            from apps.core.models import Overview
            overview = Overview.objects.get(id=overview_id)
            if new_knowledge is not None:
                overview.knowledge = new_knowledge
            if new_plan is not None:
                overview.plan = new_plan
            overview.save(update_fields=['knowledge', 'plan'])
            return f"成功更新 Overview#{overview_id} 的 knowledge 與 plan！"
        except Exception as e:
            logger.error(f"Failed to update Overview#{overview_id}: {e}")
            return f"更新 Overview 時發生錯誤: {e}"

    @method_tool
    def create_step(
        self, 
        overview_id: int, 
        command_template: str, 
        method: str, 
        description: str,
        asset_fk_field: str,
        asset_fk_value_id: int,
        parent_step_id: int = None
    ) -> str:
        """
        為自動化滲透測試流程建立一個新的執行步驟（Step）與攻擊向量（AttackVector）。
        使用這個工具根據已分析好的情報生成接下來要對目標執行的指令。

        Args:
            overview_id: 關聯的概覽 ID。
            command_template: 要執行的 CLI 命令（例如 'nmap -sV -p 80 {{ip}}'）。
            method: 使用的工具名稱 (nmap, nuclei, curl 等)。
            description: 這個步驟的說明與目的。
            asset_fk_field: 關聯的資產類型 ('ip', 'subdomain', 或 'url_result')。
            asset_fk_value_id: 關聯的資產記錄的主鍵 ID。
            parent_step_id: (Optional) 這個步驟的父步驟 ID，如果是全新發起可為空。
        """
        try:
            from apps.core.models import Step, AttackVector, Overview
            
            # 建立基底 Step
            step = Step.objects.create(
                overview_id=overview_id,
                parent_step_id=parent_step_id,
                status="PENDING"
            )
            
            # 使用 getattr 動態關聯特定的資產 (ManyToManyField)
            if asset_fk_field and asset_fk_value_id:
                m2m_mgr = getattr(step, asset_fk_field, None)
                if m2m_mgr is not None:
                    m2m_mgr.add(asset_fk_value_id)
            
            # 建立關聯的 AttackVector
            AttackVector.objects.create(
                step=step,
                method=method,
                command_template=command_template,
                description=description
            )
            
            return f"成功建立新的 Step#{step.id} 與 AttackVector ({method})！"
        except Exception as e:
            logger.error(f"Failed to create step: {e}")
            return f"建立 Step 時發生錯誤: {e}"
