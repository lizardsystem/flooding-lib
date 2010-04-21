#alphabetical order
from .models import ApprovalObjectType, ApprovalObject, ApprovalObjectState, ApprovalRule

from django.contrib import admin
from django.contrib import databrowse


class ApprovalObjectTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'type' ]

class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'permissionlevel' ]

class ApprovalObjectStateAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'date', 'creatorlog', 'successful', 'remarks' ]


#alphabetical order
admin.site.register(ApprovalObjectType, ApprovalObjectTypeAdmin)
admin.site.register(ApprovalRule, ApprovalRuleAdmin)
admin.site.register(ApprovalObjectState, ApprovalObjectStateAdmin)
admin.site.register(ApprovalObject)

