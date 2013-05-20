from project.models import *
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_group', 'doc_type', 'baseline_name', 'order', 'pk')

admin.site.register(Project,ProjectAdmin)
