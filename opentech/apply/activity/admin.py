from django.contrib import admin
from .models import Event, Message


class MessageInline(admin.TabularInline):
    model = Message
    readonly_fields = ('type', 'recipient', 'content', 'status', 'external_id')
    can_delete = False

    def has_add_permission(self, request):
        return False


class EventAdmin(admin.ModelAdmin):
    list_display = ('type', 'by', 'when', 'submission')
    list_filter = ('type', 'when')
    readonly_fields = ('type', 'submission', 'when', 'by')
    inlines = (MessageInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, *args):
        return False


admin.site.register(Event, EventAdmin)
