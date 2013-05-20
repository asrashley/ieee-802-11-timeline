from timeline.models import *
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_group', 'doc_type', 'status', 'baseline_name', 'order', 'pk')

admin.site.register(Ballot)
admin.site.register(Project,ProjectAdmin)
