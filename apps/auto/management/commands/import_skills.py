import hashlib
import os
import re

import yaml
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """將 VulnClaw Markdown 技能檔案同步至 SkillTemplate 資料表。"""

    help = "同步 VulnClaw Markdown 技能檔案至 SkillTemplate"

    DEFAULT_SOURCE_REL = "apps/auto/VulnClaw/vulnclaw/skills"
    # 父技能檔名（由 prompt 內嵌處理，不寫入 DB）
    PARENT_FILENAMES = ("SKILL.md", "waf-bypass.md")
    # 例外：這些路徑段下的 SKILL.md 不是「父技能入口」而是 DB 載入的內容
    # recon 目錄下只有 recon-playbook 一個檔案，它本身就是 documentation 技能
    NON_PARENT_SKILL_DIRS = ("recon",)

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            default=self.DEFAULT_SOURCE_REL,
            help="技能 Markdown 來源目錄（相對於 BASE_DIR）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="只顯示將要執行的動作，不寫入資料庫",
        )
        parser.add_argument(
            "--include-parents",
            action="store_true",
            default=False,
            help="是否一併匯入父技能（SKILL.md / waf-bypass.md）",
        )
        parser.add_argument(
            "--bump-on",
            choices=["hash", "always"],
            default="hash",
            help="版本遞增策略：hash（內容改變才遞增）/ always（每次都遞增）",
        )

    # ------------------------------------------------------------------
    # Markdown 解析
    # ------------------------------------------------------------------
    _FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

    def _parse_markdown(self, file_path):
        """解析 Markdown，回傳 (frontmatter_dict, body_str)。失敗回傳 (None, None)。"""
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            self.stdout.write(self.style.WARNING(f"無法讀取檔案 {file_path}: {exc}"))
            return None, None

        match = self._FRONTMATTER_RE.match(raw)
        if not match:
            self.stdout.write(self.style.WARNING(f"缺少 frontmatter，跳過: {file_path}"))
            return None, None

        yaml_block, body = match.group(1), match.group(2)
        try:
            meta = yaml.safe_load(yaml_block) or {}
        except yaml.YAMLError as exc:
            self.stdout.write(self.style.WARNING(f"YAML 解析失敗 {file_path}: {exc}"))
            return None, None

        if not isinstance(meta, dict):
            self.stdout.write(self.style.WARNING(f"frontmatter 非 dict: {file_path}"))
            return None, None

        return meta, body

    # ------------------------------------------------------------------
    # 檔案探索
    # ------------------------------------------------------------------
    def _is_parent_skill(self, file_path, rel_path):
        """判斷是否為父技能檔案。"""
        base = os.path.basename(file_path)
        normalized = rel_path.replace("\\", "/")
        # 例外：recon 等目錄的 SKILL.md 是 DB 載入內容，不是父技能入口
        parts = normalized.split("/")
        for non_parent_dir in self.NON_PARENT_SKILL_DIRS:
            if non_parent_dir in parts and base == "SKILL.md":
                return False
        if base in self.PARENT_FILENAMES:
            return True
        # 路徑段落中包含 core/waf-bypass.md
        if "core/waf-bypass.md" in normalized:
            return True
        return False

    def _extract_parent_tag(self, rel_path):
        """從目錄結構萃取 parent 標籤。

        - core/*.md            -> parent:core
        - specialized/recon/SKILL.md -> parent:recon
        - specialized/web-security-advanced/references/x.md -> parent:web-security-advanced
        """
        parts = rel_path.replace("\\", "/").split("/")
        # 找到 "specialized" 之後的下一個段落即為父分類
        if "specialized" in parts:
            idx = parts.index("specialized")
            if idx + 1 < len(parts):
                return f"parent:{parts[idx + 1]}"
        if "core" in parts:
            return "parent:core"
        # 退而求其次：取最上層目錄
        if len(parts) >= 2:
            return f"parent:{parts[0]}"
        return "parent:core"

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        try:
            # 延遲匯入，避免 startup signal 觸發時載入過早
            from apps.core.models.analyze.SkillTemplate import SkillTemplate
            from django.conf import settings

            source_dir = options["source_dir"]
            dry_run = options["dry_run"]
            include_parents = options["include_parents"]
            bump_on = options["bump_on"]

            # 解析來源目錄（允許相對於 BASE_DIR 或絕對路徑）
            base_dir = settings.BASE_DIR
            if os.path.isabs(source_dir):
                root = source_dir
            else:
                root = os.path.join(str(base_dir), source_dir)

            if not os.path.isdir(root):
                self.stdout.write(self.style.ERROR(f"來源目錄不存在: {root}"))
                return

            self.stdout.write(self.style.NOTICE(
                f"掃描來源目錄: {root}\n"
                f"  bump_on={bump_on}  dry_run={dry_run}  include_parents={include_parents}"
            ))

            md_files = []
            for dirpath, _dirs, filenames in os.walk(root):
                for fname in sorted(filenames):
                    if fname.endswith(".md"):
                        md_files.append(os.path.join(dirpath, fname))
            md_files.sort()

            scanned = created = updated = skipped_unchanged = skipped_parent = errors = 0

            for abs_path in md_files:
                scanned += 1
                rel_path = os.path.relpath(abs_path, root)

                # 父技能判斷
                if not include_parents and self._is_parent_skill(abs_path, rel_path):
                    skipped_parent += 1
                    self.stdout.write(self.style.NOTICE(
                        f"[跳過-父技能] {rel_path}"
                    ))
                    continue

                meta, body = self._parse_markdown(abs_path)
                if meta is None:
                    errors += 1
                    continue

                name = (meta.get("name") or "").strip()
                description = meta.get("description") or ""
                skill_type = meta.get("skill_type") or "documentation"
                tags = meta.get("tags") or []
                short_desc = meta.get("short_description") or ""

                if not name:
                    self.stdout.write(self.style.WARNING(
                        f"frontmatter 缺少 name 欄位，跳過: {rel_path}"
                    ))
                    errors += 1
                    continue

                if not isinstance(tags, list):
                    tags = [tags] if tags else []

                # description 長度限制（模型 clean() 強制 <= 500）
                if len(description) > 500:
                    self.stdout.write(self.style.WARNING(
                        f"description 過長（{len(description)} > 500），已截斷: {name}"
                    ))
                    description = description[:500]

                # short_description（≤80 chars）+ parent 標籤 + hash 標籤
                if not short_desc:
                    short_desc = description[:80]

                parent_tag = self._extract_parent_tag(rel_path)
                body_stripped = (body or "").strip()
                body_hash = hashlib.sha256(body_stripped.encode("utf-8")).hexdigest()
                hash_tag = f"hash:{body_hash}"

                final_tags = list(tags) + [parent_tag, hash_tag]

                # 查詢既有最新版本
                latest = (
                    SkillTemplate.objects.filter(name=name)
                    .order_by("-version")
                    .first()
                )

                action = None  # create / update / skip
                if latest is None:
                    new_version = 1
                    action = "create"
                else:
                    existing_hash = None
                    for t in latest.tags or []:
                        if isinstance(t, str) and t.startswith("hash:"):
                            existing_hash = t[len("hash:"):]
                            break
                    if bump_on == "hash" and existing_hash == body_hash:
                        action = "skip"
                        new_version = latest.version
                    else:
                        action = "update"
                        new_version = latest.version + 1

                # 跳過無變更
                if action == "skip":
                    skipped_unchanged += 1
                    self.stdout.write(self.style.NOTICE(
                        f"[跳過-無變更] {name} v{latest.version}"
                    ))
                    continue

                # 組裝紀錄
                detailed_overview = body_stripped or description
                # instructions 為模型必填欄位（clean 要求 <=2000）
                # 對 documentation 型技能，取 detailed_overview 的前段作為內容摘要
                # （而非 description 的副本，避免資訊重複）
                instructions = detailed_overview[:2000]

                skill = SkillTemplate(
                    name=name,
                    description=description,
                    short_description=short_desc[:200],
                    detailed_overview=detailed_overview,
                    skill_type=skill_type,
                    tags=final_tags,
                    version=new_version,
                    is_deprecated=False,
                    instructions=instructions,
                    language="python",
                )

                tag_prefix = "[DRY RUN] " if dry_run else ""

                # 驗證
                try:
                    skill.full_clean()
                except Exception as exc:  # noqa: BLE001 - 任何驗證錯誤皆記錄並跳過
                    errors += 1
                    self.stdout.write(self.style.ERROR(
                        f"{tag_prefix}驗證失敗 {name} v{new_version}: {exc}"
                    ))
                    continue

                if dry_run:
                    if action == "create":
                        created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"{tag_prefix}[新增] {name} v1  ({rel_path})"
                        ))
                    else:
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"{tag_prefix}[版本更新] {name} v{latest.version} -> v{new_version}  ({rel_path})"
                        ))
                    continue

                # 實際寫入
                try:
                    skill.save()
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    self.stdout.write(self.style.ERROR(
                        f"儲存失敗 {name} v{new_version}: {exc}"
                    ))
                    continue

                # 更新動作需將舊版本標記為 deprecated
                if action == "update" and latest is not None and not latest.is_deprecated:
                    SkillTemplate.objects.filter(pk=latest.pk).update(is_deprecated=True)

                if action == "create":
                    created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"[新增] {name} v1  ({rel_path})"
                    ))
                else:
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"[版本更新] {name} v{latest.version} -> v{new_version}  ({rel_path})"
                    ))

            # 摘要
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("=== VulnClaw Skills 同步完成 ==="))
            self.stdout.write(f"掃描: {scanned} 個檔案")
            self.stdout.write(f"新增: {created} 個")
            self.stdout.write(f"版本更新: {updated} 個")
            self.stdout.write(f"跳過(無變更): {skipped_unchanged} 個")
            self.stdout.write(f"跳過(父技能): {skipped_parent} 個")
            self.stdout.write(f"錯誤: {errors} 個")
            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY RUN] 未寫入任何資料"))

        except Exception as exc:  # noqa: BLE001 - 不讓 startup signal 呼叫者崩潰
            self.stdout.write(self.style.ERROR(f"import_skills 發生未預期錯誤: {exc}"))
            try:
                import logging
                logging.getLogger(__name__).exception("import_skills failed")
            except Exception:  # noqa: BLE001
                pass
