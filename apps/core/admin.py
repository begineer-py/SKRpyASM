from django.contrib import admin
from apps.core.models import (
    IP,
    URLResult,
    Subdomain,
    URLScan,
    Form,
    JavaScriptFile,
    Endpoint,
    Link,
    MetaTag,
    Comment,
    Iframe,
    NmapScan,
    Port,
    SubfinderScan,
    Overview,
    Payload,
    Verification,
)

admin.site.register(IP)
admin.site.register(URLResult)
admin.site.register(Subdomain)
admin.site.register(URLScan)
admin.site.register(Form)
admin.site.register(JavaScriptFile)
admin.site.register(Endpoint)
admin.site.register(Link)
admin.site.register(MetaTag)
admin.site.register(Comment)
admin.site.register(Iframe)
admin.site.register(NmapScan)
admin.site.register(Port)
admin.site.register(SubfinderScan)
admin.site.register(Overview)
admin.site.register(Payload)
admin.site.register(Verification)
