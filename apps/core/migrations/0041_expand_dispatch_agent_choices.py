# Generated manually for SubAgentDispatch.DISPATCH_AGENT_CHOICES expansion (G1)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0040_add_action_to_vulnerability"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subagentdispatch",
            name="sub_agent_type",
            field=models.CharField(
                choices=[
                    ("automation_agent", "Automation Agent"),
                    ("recon_agent", "Recon Agent"),
                    ("post_exploit_agent", "Post-Exploit Agent"),
                    ("reporting_agent", "Reporting Agent"),
                ],
                help_text="子代理類型",
                max_length=50,
            ),
        ),
    ]
