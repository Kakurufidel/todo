from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(Reminder)
admin.site.register(TimeLog)