from django.db import migrations


def fix_flat_compressed_content(apps, schema_editor):
    """修復舊的扁平格式 compressed_content — 包成 LangChain 巢狀格式 + 補 tool_call_id。"""
    Message = apps.get_model("core", "Message")
    db_alias = schema_editor.connection.alias

    bad_msgs = (
        Message.objects.using(db_alias)
        .filter(
            compression_applied=True,
            is_tool_output=True,
        )
        .exclude(compressed_content__isnull=True)
    )

    fixed = 0
    for msg in bad_msgs.iterator():
        cc = msg.compressed_content
        if not isinstance(cc, dict):
            continue
        if "data" in cc:
            continue

        if cc.get("type") != "tool":
            continue

        content = cc.get("content", "")
        name = cc.get("name") or "unknown"

        orig = msg.message if isinstance(msg.message, dict) else {}
        orig_data_raw = orig.get("data")
        orig_data = orig_data_raw if isinstance(orig_data_raw, dict) else {}
        tool_call_id = orig_data.get("tool_call_id") or f"compressed_{msg.id}"
        msg_id = orig_data.get("id")

        msg.compressed_content = {
            "type": "tool",
            "data": {
                "content": content,
                "name": name,
                "tool_call_id": tool_call_id,
                "id": msg_id,
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "tool",
                "artifact": None,
                "status": "success",
            },
        }
        msg.save(update_fields=["compressed_content"])
        fixed += 1

    if fixed:
        print(f"\n  Fixed {fixed} flat-format compressed_content records")


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_remove_overview_plan_and_attackvector_dup_description"),
    ]

    operations = [
        migrations.RunPython(fix_flat_compressed_content, reverse_fix),
    ]
