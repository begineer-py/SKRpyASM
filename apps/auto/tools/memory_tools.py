import logging
from django.utils import timezone
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class MemoryMixin:
    """
    Memory & Context Compression Tools Mixin
    Provides tools for saving long-term content, managing notes, and compressing large outputs.
    """

    def _generate_summary(self, content: str, max_chars: int = 500) -> str:
        """內部工具：呼叫輕量 LLM 對超長內容產生摘要。"""
        try:
            from apps.core.llms import get_llm_instance
            from langchain_core.messages import HumanMessage

            llm = get_llm_instance(agent_id="compression_agent", temperature=0)
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

    def _get_compression_llm(self):
        """Get configured LLM for compression tasks (configurable via compression_agent)."""
        from apps.core.llms import get_llm_instance
        return get_llm_instance(agent_id="compression_agent", temperature=0)

    def _generate_tool_summary(self, tool_name: str, content: str, guidance: str, llm) -> str:
        """Generate a concise summary of a tool output for compression."""
        from langchain_core.messages import HumanMessage

        truncated = str(content)[:5000]
        prompt = (
            f"Summarize this {tool_name} tool output concisely (max 300 chars).\n"
            f"Preserve key technical details (IPs, ports, URLs, findings, error messages).\n"
        )
        if guidance:
            prompt += f"Agent guidance: {guidance}\n"
        prompt += f"\nOutput:\n{truncated}\n\nSummary:"

        try:
            resp = llm.invoke([HumanMessage(content=prompt)])
            summary = resp.content if hasattr(resp, 'content') else str(resp)
            return summary.strip()[:500]
        except Exception as e:
            logger.warning(f"Tool summary failed for {tool_name}: {e}")
            return f"{tool_name}: {truncated[:150]}..."

    @method_tool
    def review_chunks(self) -> str:
        """
        [Memory Management] 檢視對話歷史並產生概覽與可壓縮區塊。

        系統會：
        1. 閱讀所有 Messages 並產生戰略性概覽（GlobalContextOverview）
        2. 將對話劃分為邏輯區塊（每個 THINK→ACT→RESULT 循環為一組）
        3. 顯示每個區塊的摘要資訊

        檢視後，對每個你想處理的區塊呼叫 decide_chunk(chunk_index, strategy)，
        最後呼叫 apply_compression() 套用所有決定。
        """
        thread = getattr(self, '_thread', None)
        if not thread:
            return "錯誤：無法取得當前 Thread。"

        msg_count = thread.messages.count()
        if msg_count < 5:
            return f"對話僅 {msg_count} 條訊息，尚無需壓縮。"

        llm = self._get_compression_llm()

        # Step 1: Generate GlobalContextOverview (reading all messages first)
        from apps.auto.compression.overview_generator import GlobalOverviewGenerator

        generator = GlobalOverviewGenerator(thread, llm)
        overview = generator.generate(force=True)

        # Step 2: Clear old chunks, re-divide
        thread.compression_chunks.all().delete()

        from apps.auto.compression.chunk_divider import ChunkDivider

        divider = ChunkDivider(thread)
        chunks = divider.divide()
        saved_chunks = divider.save_chunks(chunks)

        # Step 3: Format output
        lines = []
        lines.append("=== GLOBAL CONTEXT OVERVIEW ===")
        lines.append(f"Mission: {overview.mission}")
        lines.append(f"Phase: {overview.current_phase}")
        if overview.confirmed_vulnerabilities:
            lines.append(f"Confirmed Vulns: {len(overview.confirmed_vulnerabilities)}")
            for v in overview.confirmed_vulnerabilities[:5]:
                title = v.get('title', v) if isinstance(v, dict) else v
                lines.append(f"  - {title}")
        if overview.critical_artifacts:
            lines.append(f"Critical Artifacts: {len(overview.critical_artifacts)}")
        if overview.metrics:
            lines.append(f"Metrics: {overview.metrics}")
        lines.append("")

        lines.append("=== COMPRESSIBLE CHUNKS ===")
        lines.append(f"{'Index':<6} {'Messages':<14} {'Tools':<22} {'Size':<10} Strategy")
        lines.append("-" * 80)

        for c in saved_chunks:
            tool_list = c.tool_calls or []
            tools_str = ", ".join(str(t) for t in tool_list[:3])
            if len(tool_list) > 3:
                tools_str += f" +{len(tool_list)-3}"
            size = len(str(c.original_content)) if c.original_content else 0
            size_str = f"{size:,}" if size >= 1000 else str(size)
            lines.append(
                f"{c.chunk_index:<6} #{c.start_message_id}-#{c.end_message_id:<9} "
                f"{tools_str:<22} {size_str:<10} PENDING"
            )

        lines.append("")
        lines.append(
            "Call decide_chunk(chunk_index=N, strategy='RETAIN|TEXTUALIZE|DISCARD') "
            "for each chunk you want to process."
        )
        lines.append("Then call apply_compression() to finalize.")

        return "\n".join(lines)

    @method_tool
    def decide_chunk(self, chunk_index: int, strategy: str, guidance: str = "") -> str:
        """
        [Memory Management] 決定某個區塊的保留策略。

        Args:
            chunk_index: review_chunks() 回傳的區塊編號
            strategy: 保留策略
                RETAIN - 完整保留（重要發現/漏洞資訊）
                TEXTUALIZE - 壓縮為摘要（已記錄在 overview 中的掃描結果）
                DISCARD - 捨棄工具輸出（不相關或已過時的內容）
            guidance: (選填) 對壓縮助手的提示，例如「保留 SQL 語句和錯誤訊息」
        """
        thread = getattr(self, '_thread', None)
        if not thread:
            return "錯誤：無法取得當前 Thread。"

        strategy = strategy.upper()
        if strategy not in ('RETAIN', 'TEXTUALIZE', 'DISCARD'):
            return f"不支援的策略 '{strategy}'。請使用 RETAIN / TEXTUALIZE / DISCARD。"

        try:
            chunk = thread.compression_chunks.get(chunk_index=chunk_index)
        except Exception:
            return f"找不到 chunk #{chunk_index}。請先呼叫 review_chunks()。"

        from apps.core.models.ai_models import Message

        if strategy == 'RETAIN':
            chunk.strategy = 'RETAIN'
            chunk.save(update_fields=['strategy'])
            return f"Chunk#{chunk_index} 策略設為 RETAIN — 完整保留。"

        if strategy == 'DISCARD':
            messages = Message.objects.filter(
                thread=thread,
                id__gte=chunk.start_message_id,
                id__lte=chunk.end_message_id,
                role="tool_result",
            )
            discarded = 0
            for msg in messages:
                from apps.auto.compression.message_utils import build_compressed_tool_dict
                msg.compressed_content = build_compressed_tool_dict(
                    msg,
                    compressed_content_str="[Agent discarded this tool output]",
                )
                msg.compression_applied = True
                msg.save(update_fields=['compressed_content', 'compression_applied'])
                discarded += 1

            chunk.strategy = 'DISCARD'
            chunk.save(update_fields=['strategy'])
            return f"Chunk#{chunk_index} 設為 DISCARD — 已捨棄 {discarded} 個工具輸出。"

        if strategy == 'TEXTUALIZE':
            llm = self._get_compression_llm()

            messages = Message.objects.filter(
                thread=thread,
                id__gte=chunk.start_message_id,
                id__lte=chunk.end_message_id,
                role="tool_result",
            )
            textualized = 0
            total_size = 0
            compressed_size = 0

            for msg in messages:
                from apps.auto.compression.message_utils import extract_msg_fields, build_compressed_tool_dict
                fields = extract_msg_fields(msg)
                tool_name = fields.get("name") or "unknown"
                output_content = fields.get("content") or ""
                output_size = len(output_content)
                total_size += output_size

                summary = self._generate_tool_summary(tool_name, output_content, guidance, llm)

                msg.compressed_content = build_compressed_tool_dict(
                    msg,
                    compressed_content_str=(
                        f"[Agent compressed - original: {output_size} chars]\n"
                        f"Summary: {summary}"
                    ),
                    tool_name=tool_name,
                )
                msg.compression_applied = True
                msg.save(update_fields=['compressed_content', 'compression_applied'])
                compressed_size += len(summary)
                textualized += 1

            chunk.strategy = 'TEXTUALIZE'
            chunk.save(update_fields=['strategy'])

            saved = total_size - compressed_size
            return (
                f"Chunk#{chunk_index} 設為 TEXTUALIZE — "
                f"已壓縮 {textualized} 個工具輸出 "
                f"({total_size:,} → {compressed_size:,} chars, -{saved:,} chars)"
            )

        return f"未知錯誤。"

    @method_tool
    def apply_compression(self) -> str:
        """
        [Memory Management] 套用所有區塊決定，更新壓縮狀態。

        在所有 decide_chunk() 呼叫完成後執行此工具。
        下次對話載入時，GlobalContextOverview 會自動注入 system prompt。
        """
        thread = getattr(self, '_thread', None)
        if not thread:
            return "錯誤：無法取得當前 Thread。"

        from apps.core.models import ThreadCompressionState

        chunks = thread.compression_chunks.filter(strategy__in=['RETAIN', 'TEXTUALIZE', 'DISCARD'])
        pending = thread.compression_chunks.filter(strategy='PENDING')

        if not chunks.exists():
            return "沒有已決定的區塊。請先呼叫 decide_chunk()。"

        state, _ = ThreadCompressionState.objects.get_or_create(thread=thread)
        state.total_message_count = thread.messages.count()
        state.requires_compression = False
        state.last_compressed_at = timezone.now()

        summary = state.compression_summary or {}
        summary['last_compression'] = {
            'timestamp': state.last_compressed_at.isoformat(),
            'chunks_decided': chunks.count(),
            'chunks_pending': pending.count(),
        }
        state.compression_summary = summary
        state.save()

        lines = []
        lines.append(f"=== 壓縮完成 ===")
        lines.append(f"已處理 {chunks.count()} 個區塊（{pending.count()} 個待決定）")
        lines.append("")
        for c in chunks:
            lines.append(f"  Chunk#{c.chunk_index}: {c.strategy}")
        lines.append("")
        lines.append("GlobalContextOverview 已更新。下次對話時自動載入。")
        lines.append("Tip: 若仍有 PENDING 區塊，可繼續呼叫 decide_chunk()。")

        return "\n".join(lines)

    @method_tool
    def save_long_content(self, content: str, source_type: str = "other", source_url: str = None) -> str:
        """
        [Context Compression] 當你獲取到超長的輸出（> 2000 字的 HTML/Stack Trace/報告）時，
        呼叫此工具將它存入長期記憶庫 (ContentBlob)。系統會自動產生 AI 摘要，你只需要記住 blob_id。
        之後若需要深入查看原文，再使用 read_content_blob。

        Args:
            content: 要儲存的超長原始內容
            source_type: 來源類型 ('curl', 'crawler', 'nuclei', 'other')
            source_url: 來源網址 (選填)
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
        )
        # Fix D: generate page_breakdown for large content
        if len(content) > 12000:
            try:
                from apps.core.llms import get_llm_instance
                from langchain_core.messages import HumanMessage
                import json
                _llm = get_llm_instance(agent_id="compression_agent", temperature=0)
                _prompt = (
                    "你是一個文檔結構分析專家。請將以下內容按語義結構拆分為多個頁面(page)。\n"
                    "要求：\n"
                    "1. 按內容主題自然分頁（而非按字符硬切）\n"
                    "2. 每頁提供一個簡短的 title（20 字以內）\n"
                    "3. 每頁 content 不超過 4000 字\n"
                    "4. 輸出為 JSON 數組格式：[{\"title\": \"...\", \"content\": \"...\"}]\n"
                    "5. 只輸出 JSON，不要額外的解釋\n\n"
                    f"=== 原始內容（截取前 50000 字）===\n{content[:50000]}"
                )
                _resp = _llm.invoke([HumanMessage(content=_prompt)])
                _text = _resp.content if hasattr(_resp, 'content') else str(_resp)
                if '```json' in _text:
                    _text = _text.split('```json')[1].split('```')[0].strip()
                elif '```' in _text:
                    _text = _text.split('```')[1].split('```')[0].strip()
                _pages = json.loads(_text)
                if isinstance(_pages, list) and _pages:
                    blob.page_breakdown = _pages
                    blob.save(update_fields=['page_breakdown'])
            except Exception as _e:
                logger.warning(f"Page breakdown generation skipped in save_long_content: {_e}")

        try:
            from apps.core.models import ExecutionGraph, ExecutionNode
            from apps.core.services import ExecutionService

            graph = getattr(self, "_execution_graph", None)
            node = getattr(self, "_current_execution_node", None)
            if graph is None:
                graph_id = getattr(self, "_current_execution_graph_id", None)
                graph = ExecutionGraph.objects.filter(id=graph_id).first() if graph_id else None
            if node is None:
                node_id = getattr(self, "_current_execution_node_id", None)
                node = ExecutionNode.objects.filter(id=node_id).first() if node_id else None
            if graph is not None:
                ExecutionService.attach_artifact(
                    graph=graph,
                    node=node,
                    artifact_type="content_blob",
                    name=f"ContentBlob #{blob.id}",
                    content=ai_summary,
                    data={"blob_id": blob.id, "source_type": source_type, "source_url": source_url},
                    content_blob=blob,
                )
        except Exception as artifact_error:
            logger.warning("Failed to attach ContentBlob #%s to execution graph: %s", blob.id, artifact_error)
        _pages = getattr(blob, 'page_breakdown', None)
        _page_hint = ""
        if _pages and isinstance(_pages, list) and len(_pages) > 0:
            _page_hint = (
                f"\nPages: {len(_pages)} pages available.\n"
                f"Use read_content_blob(blob_id={blob.id}, page=N) to read a specific page (1-{len(_pages)}).\n"
            )
        return (
            f"[Long Output Saved] blob_id={blob.id} | Size: {blob.content_size} chars\n"
            f"Summary: {ai_summary}\n"
            f"{_page_hint}"
            f"若需要深入閱讀原文，請呼叫 read_content_blob(blob_id={blob.id})"
        )

    @method_tool
    def read_content_blob(self, blob_id: int, focus_query: str = None, page: int = None) -> str:
        """
        [Context Compression] 讀取長期記憶中的內容。
        - 不帶 focus_query 與 page：回傳先前自動生成的 AI 摘要 (ai_summary)。
        - 帶 page=N：回傳該頁的結構化內容（限 page_breakdown 已產生的 blob）。
        - 帶 focus_query：啟動壓縮助手，針對原始全文進行聚焦式提取。
          例如 focus_query='幫我找出裡面的 SQL 語法錯誤' 會讓助手只提取相關段落。

        Args:
            blob_id: ContentBlob 的 ID
            focus_query: (選填) 聚焦問題，讓系統針對原文提取特定資訊
            page: (選填) 頁碼（從 1 開始），僅在 blob 有 page_breakdown 時可用
        """
        from apps.core.models.analyze.ContentBlob import ContentBlob

        try:
            blob = ContentBlob.objects.get(id=blob_id)
        except ContentBlob.DoesNotExist:
            return f"ContentBlob ID {blob_id} 不存在。"

        # Fix D: structured page retrieval
        if page is not None and blob.page_breakdown:
            try:
                idx = page - 1
                if 0 <= idx < len(blob.page_breakdown):
                    p = blob.page_breakdown[idx]
                    return (
                        f"=== ContentBlob #{blob.id} — Page {page}/{len(blob.page_breakdown)} ===\n"
                        f"Title: {p.get('title', 'Untitled')}\n\n"
                        f"{p.get('content', '')}"
                    )
                else:
                    available = "\n".join(
                        f"  Page {i+1}: {p.get('title', 'Untitled')}"
                        for i, p in enumerate(blob.page_breakdown)
                    )
                    return (
                        f"Page index out of range. Valid pages: 1-{len(blob.page_breakdown)}\n"
                        f"Available pages:\n{available}"
                    )
            except (IndexError, TypeError) as e:
                return f"Page retrieval failed: {e}"

        if page is not None and not blob.page_breakdown:
            return (
                f"=== ContentBlob #{blob.id} ===\n"
                f"This blob has no page_breakdown. Use `read_content_blob(blob_id={blob_id})` without `page` "
                f"or with `focus_query` to read the content."
            )

        if not focus_query:
            intro = f"=== ContentBlob #{blob.id} Summary ===\n"
            if blob.page_breakdown:
                page_count = len(blob.page_breakdown)
                intro += f"Pages available: {page_count}\n"
            intro += f"Source: {blob.source_type} | URL: {blob.source_url or 'N/A'} | Size: {blob.content_size} chars\n\n"
            return intro + (blob.ai_summary or 'No summary available.')

        # 帶 focus_query：啟動聚焦式壓縮
        try:
            from apps.core.llms import get_llm_instance
            from langchain_core.messages import HumanMessage

            llm = get_llm_instance(agent_id="compression_agent", temperature=0)
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
    def write_recon_note(self, overview_id: int = None, title: str = "", content: str = "") -> str:
        """
        快速將偵察發現（例如 curl 的回應、表單結構、注入測試結果）儲存為 execution artifact。
        在完成任何手動操作（如 run_command 執行 curl）後，立刻呼叫此工具保存結果。

        此工具只記錄 ExecutionArtifact，不建立 AttackVector。
        若需要追蹤攻擊向量，請使用 add_action 建立結構化的 Action + AttackVector。

        Args:
            overview_id: (Optional) 當前 Overview 的 ID。自動注入。
            title: 此發現的簡短標題 (e.g., 'POST /register – SQLi 測試結果')。
            content: 詳細的發現內容（可包含 curl 回應、觀察到的行為、評估等）。
        """
        try:
            from apps.core.models import ExecutionGraph
            from apps.core.services import ExecutionService
            from apps.core.models.analyze.overview import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"❌ 錯誤: Overview ID {overview_id} 不存在。請確認你使用 get_target_context 拿到的 Active Overview ID。"

            graph = getattr(self, "_execution_graph", None)
            node = getattr(self, "_current_execution_node", None)
            if graph is None:
                graph_id = getattr(self, "_current_execution_graph_id", None)
                graph = ExecutionGraph.objects.filter(id=graph_id).first() if graph_id else None

            if graph is not None:
                ExecutionService.emit_event(
                    graph=graph,
                    node=node,
                    event_type="recon_note_recorded",
                    status="completed",
                    content=title or "Recon note recorded",
                    payload={"overview_id": overview_id, "title": title, "content_preview": content[:1000]},
                )
                artifact = ExecutionService.attach_artifact(
                    graph=graph,
                    node=node,
                    artifact_type="recon_note",
                    name=title[:255] or "Recon Note",
                    content=content,
                    data={"overview_id": overview_id, "title": title},
                )
            else:
                artifact = None

            return f"✅ 已記錄偵察發現至 ExecutionArtifact#{getattr(artifact, 'id', 'N/A')}。"
        except Exception as e:
            logger.error(f"Failed to write recon note for overview {overview_id}: {e}")
            return f"記錄偵察筆記失敗: {e}"
