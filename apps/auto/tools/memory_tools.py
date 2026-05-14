import logging
from django_ai_assistant import method_tool

logger = logging.getLogger(__name__)


class MemoryMixin:
    """
    Memory & Context Compression Tools Mixin
    Provides tools for saving long-term content, managing notes, and compressing large outputs.
    """

    def _generate_summary(self, content: str, max_chars: int = 500) -> str:
        """內部工具：呼叫輕量 LLM 對超長內容產生摘要。"""
        try:
            from langchain_mistralai import ChatMistralAI
            from langchain_core.messages import HumanMessage

            llm = ChatMistralAI(model="mistral-small-2503", temperature=0, max_tokens=600)
            prompt = (
                "你是一個專業的安全分析師。以下是一段超長的工具輸出（可能是 HTML、Stack Trace、或掃描報告）。"
                "請用繁體中文產生一份精簡摘要（最多 500 字），重點提取：\n"
                "1. 主要技術棧或框架\n"
                "2. 任何錯誤訊息、異常、或安全漏洞線索\n"
                "3. 表單、端點、敏感路徑等\n"
                "4. 其他值得注意的情報\n\n"
                f"=== 原始內容（截取前 30000 字）===\n{content[:30000]}"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            return resp.content[:max_chars]
        except Exception as e:
            logger.error(f"Auto-summary generation failed: {e}")
            return f"[Auto-summary failed: {e}]"

    @method_tool
    def save_long_content(self, content: str, source_type: str = "other", source_url: str = None, step_id: int = None) -> str:
        """
        [Context Compression] 當你獲取到超長的輸出（> 2000 字的 HTML/Stack Trace/報告）時，
        呼叫此工具將它存入長期記憶庫 (ContentBlob)。系統會自動產生 AI 摘要，你只需要記住 blob_id。
        之後若需要深入查看原文，再使用 read_content_blob。

        Args:
            content: 要儲存的超長原始內容
            source_type: 來源類型 ('curl', 'crawler', 'nuclei', 'other')
            source_url: 來源網址 (選填)
            step_id: 關聯的 Step ID (選填)
        """
        from apps.core.models.analyze.ContentBlob import ContentBlob

        # 產生 AI 摘要
        ai_summary = self._generate_summary(content)

        blob = ContentBlob.objects.create(
            raw_content=content,
            content_size=len(content),
            ai_summary=ai_summary,
            source_type=source_type,
            source_url=source_url,
            step_id=step_id
        )
        return (
            f"[Long Output Saved] blob_id={blob.id} | Size: {blob.content_size} chars\n"
            f"Summary: {ai_summary}\n\n"
            f"若需要深入閱讀原文，請呼叫 read_content_blob(blob_id={blob.id})"
        )

    @method_tool
    def read_content_blob(self, blob_id: int, focus_query: str = None) -> str:
        """
        [Context Compression] 讀取長期記憶中的內容。
        - 不帶 focus_query：回傳先前自動生成的 AI 摘要 (ai_summary)。
        - 帶 focus_query：啟動壓縮助手，針對原始全文進行聚焦式提取。
          例如 focus_query='幫我找出裡面的 SQL 語法錯誤' 會讓助手只提取相關段落。

        Args:
            blob_id: ContentBlob 的 ID
            focus_query: (選填) 聚焦問題，讓系統針對原文提取特定資訊
        """
        from apps.core.models.analyze.ContentBlob import ContentBlob

        try:
            blob = ContentBlob.objects.get(id=blob_id)
        except ContentBlob.DoesNotExist:
            return f"ContentBlob ID {blob_id} 不存在。"

        if not focus_query:
            return (
                f"=== ContentBlob #{blob.id} Summary ===\n"
                f"Source: {blob.source_type} | URL: {blob.source_url or 'N/A'} | Size: {blob.content_size} chars\n\n"
                f"{blob.ai_summary or 'No summary available.'}"
            )

        # 帶 focus_query：啟動聚焦式壓縮
        try:
            from langchain_mistralai import ChatMistralAI
            from langchain_core.messages import HumanMessage

            llm = ChatMistralAI(model="mistral-small-2503", temperature=0, max_tokens=800)
            prompt = (
                f"你是一個安全分析師。以下是一段超長的內容（{blob.content_size} 字），"
                f"請針對以下問題進行聚焦式提取（最多 800 字）：\n"
                f"問題：{focus_query}\n\n"
                f"=== 原始內容（截取前 50000 字）===\n{blob.raw_content[:50000]}"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            return f"=== Focused Analysis for Blob #{blob.id} ===\nQuery: {focus_query}\n\n{resp.content}"
        except Exception as e:
            logger.error(f"Focused read failed for blob {blob_id}: {e}")
            return f"聚焦分析失敗: {e}. 摘要: {blob.ai_summary}"

    @method_tool
    def write_recon_note(self, overview_id: int, title: str, content: str) -> str:
        """
        快速將偵察發現（例如 curl 的回應、表單結構、注入測試結果）儲存為一個新的 Step + StepNote。
        在完成任何手動操作（如 run_command 執行 curl）後，立刻呼叫此工具保存結果。

        Args:
            overview_id: 當前 Overview 的 ID。
            title: 此發現的簡短標題 (e.g., 'POST /register – SQLi 測試結果')。
            content: 詳細的發現內容（可包含 curl 回應、觀察到的行為、評估等）。
        """
        try:
            from apps.core.models.analyze.Step import Step, StepNote
            from apps.core.models.analyze.overview import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"❌ 錯誤: Overview ID {overview_id} 不存在。請確認你使用 get_target_context 拿到的 Active Overview ID。"
            
            step = Step.objects.create(overview_id=overview_id, status="COMPLETED")
            StepNote.objects.create(step=step, content=f"[{title}]\n\n{content}")
            return f"✅ 已記錄偵察發現至 Step#{step.id} 的 StepNote。"
        except Exception as e:
            logger.error(f"Failed to write recon note for overview {overview_id}: {e}")
            return f"記錄偵察筆記失敗: {e}"
