"""
共用分頁服務 — 將超長內容按語義結構拆分為多個頁面。

統一原本散落在兩處的重複邏輯：
- apps/ai_assistant/helpers/assistants.py:481-517 (_generate_page_breakdown)
- apps/auto/tools/memory_tools.py:316-343 (save_long_content inline)

被以下元件使用：
- ContentBlob.page_breakdown 生成
- OverviewPage.page_breakdown 生成
- compress_tool_outputs 節點
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 觸發分頁的字元門檻
PAGE_BREAKDOWN_THRESHOLD = 12000
# 每頁最大字元數
MAX_PAGE_SIZE = 4000
# 送入 LLM 的最大字元數（避免過大 prompt）
MAX_LLM_INPUT = 50000


def generate_page_breakdown(content: str, llm=None) -> list:
    """
    使用 LLM 將超長內容拆分為結構化頁面。

    Args:
        content: 要拆分的原始內容
        llm: 可選的 LangChain LLM 實例（若不提供會嘗試 compression_agent）

    Returns:
        [{"title": str, "content": str}, ...] — 每頁 title ≤20 字、content ≤4000 字。
        失敗時回傳空 list []。
    """
    if not content or len(content) < PAGE_BREAKDOWN_THRESHOLD:
        return []

    try:
        if llm is None:
            from apps.core.llms import get_llm_instance
            try:
                llm = get_llm_instance(agent_id="compression_agent", temperature=0)
            except Exception:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(temperature=0, max_tokens=4000)

        from langchain_core.messages import HumanMessage

        prompt = (
            "你是一個文檔結構分析專家。請將以下內容按語義結構拆分為多個頁面(page)。\n"
            "要求：\n"
            "1. 按內容主題自然分頁（而非按字符硬切）\n"
            "2. 每頁提供一個簡短的 title（20 字以內）\n"
            f"3. 每頁 content 不超過 {MAX_PAGE_SIZE} 字\n"
            "4. 輸出為 JSON 數組格式：[{\"title\": \"...\", \"content\": \"...\"}]\n"
            "5. 只輸出 JSON，不要額外的解釋\n\n"
            f"=== 原始內容（截取前 {MAX_LLM_INPUT} 字）===\n{content[:MAX_LLM_INPUT]}"
        )
        resp = llm.invoke([HumanMessage(content=prompt)])
        text = resp.content if hasattr(resp, 'content') else str(resp)
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        pages = json.loads(text)
        return pages if isinstance(pages, list) else []
    except Exception as e:
        logger.error(f"Page breakdown generation failed: {e}")
        return []


def maybe_generate_page_breakdown(content: str, llm=None) -> Optional[list]:
    """
    便利函式：只有當 content 夠長時才生成 page_breakdown，否則回傳 None。
    用於 ContentBlob / OverviewPage 儲存時自動觸發。
    """
    pages = generate_page_breakdown(content, llm=llm)
    return pages if pages else None


def read_page(page_breakdown: list, page_num: int, blob_id: Optional[int] = None) -> str:
    """
    從 page_breakdown 讀取指定頁面的內容。

    Args:
        page_breakdown: [{"title": str, "content": str}, ...]
        page_num: 1-indexed 頁碼
        blob_id: 可選，用於錯誤訊息標識

    Returns:
        該頁的格式化內容字串
    """
    if not page_breakdown:
        id_label = f" #{blob_id}" if blob_id else ""
        return f"This content{id_label} has no page_breakdown."

    idx = page_num - 1
    if 0 <= idx < len(page_breakdown):
        p = page_breakdown[idx]
        id_label = f" #{blob_id}" if blob_id else ""
        return (
            f"=== Page {page_num}/{len(page_breakdown)}{id_label} ===\n"
            f"Title: {p.get('title', 'Untitled')}\n\n"
            f"{p.get('content', '')}"
        )
    # 超出範圍 — 列出可用頁面
    available = "\n".join(
        f"  Page {i+1}: {p.get('title', 'Untitled')[:50]}"
        for i, p in enumerate(page_breakdown)
    )
    return (
        f"Page {page_num} out of range. Valid pages: 1-{len(page_breakdown)}.\n"
        f"Available pages:\n{available}"
    )


def list_pages_overview(page_breakdown: list) -> str:
    """產生所有頁面的摘要列表（title + content 前 100 字）。"""
    if not page_breakdown:
        return "(no pages)"
    lines = []
    for i, p in enumerate(page_breakdown, 1):
        preview = (p.get('content', '') or '')[:100].replace('\n', ' ')
        lines.append(f"  Page {i}: {p.get('title', 'Untitled')} — {preview}...")
    return f"{len(page_breakdown)} pages:\n" + "\n".join(lines)
