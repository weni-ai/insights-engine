from django.contrib import admin

from insights.feedback.models import Survey


class SurveyAdmin(admin.ModelAdmin):
    list_display = ("start", "end")
    search_fields = ("start", "end")
    list_filter = ("start", "end")


admin.site.register(Survey, SurveyAdmin)
