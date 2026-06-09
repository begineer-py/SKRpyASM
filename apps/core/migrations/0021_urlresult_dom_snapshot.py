from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_executiongraph_executionnode_executionevent_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="urlresult",
            name="dom_snapshot",
            field=models.TextField(
                blank=True,
                help_text="截斷後的 DOM 樹摘要，供 AI 快速判讀頁面結構。",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="historicalurlresult",
            name="dom_snapshot",
            field=models.TextField(
                blank=True,
                help_text="截斷後的 DOM 樹摘要，供 AI 快速判讀頁面結構。",
                null=True,
            ),
        ),
    ]
