from django.db import models

class Step(models.Model):
    # 關聯到具體資產
    ip = models.ForeignKey("core.IP", on_delete=models.CASCADE, null=True, blank=True, related_name="steps")
    subdomain = models.ForeignKey("core.Subdomain", on_delete=models.CASCADE, null=True, blank=True, related_name="steps")
    url_result = models.ForeignKey("core.URLResult", on_delete=models.CASCADE, null=True, blank=True, related_name="steps")
    
    order = models.PositiveIntegerField(default=1)
    command_template = models.TextField(help_text="執行命令模板，如 'nmap -p {port} {ip}'")
    expectation = models.TextField(help_text="預期的結果或輸出關鍵字")
    note = models.TextField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    
    created_at = models.DateTimeField(auto_now_add=True)

class Payload(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='payloads')
    content = models.TextField()
    platform = models.CharField(max_length=100)

class Method(models.Model): # Naming fix: method -> Method
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='methods')
    name = models.CharField(max_length=100)
    description = models.TextField()

class Verification(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='verifications')
    pattern = models.TextField()
    match_type = models.CharField(max_length=100)