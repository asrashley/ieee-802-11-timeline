from ballot.models import *
from django.contrib import admin

class BallotAdmin(admin.ModelAdmin):
    list_display = ('number', 'ballot_type', 'project_name', 'draft', 'opened', 'closed')

admin.site.register(Ballot, BallotAdmin)
