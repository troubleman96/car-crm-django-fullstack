"""
chatbot/admin.py — Django admin configuration for the Chatbot app.

This file registers ChatSession and ChatMessage with the Django admin
interface, allowing the sales team to view and manage chat
conversations through the /admin/ web panel.

Key features:
  - ChatMessageInline: Shows messages inline on the Session edit page.
  - ChatSessionAdmin:  Lists sessions with key details (phone, lead).
  - ChatMessageAdmin:  Shows a truncated "preview" of each message.

Note on can_delete = False in the inline:
    We set can_delete = False on ChatMessageInline because deleting
    individual messages from a session would corrupt the conversation
    history — you'd lose parts of the discussion. The whole session
    can still be deleted from the session admin page.
"""

from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    """
    Displays ChatMessage records as a table inside the ChatSession
    admin page.

    This lets admin users see the entire conversation at a glance
    when viewing a session, rather than having to click through to
    a separate message list page.

    Configuration choices:
      - extra = 0: No empty "add new" rows (messages are typically
        created automatically by the chatbot, not manually).
      - readonly_fields: The sender, message, and timestamp should
        not be editable in the inline — they're historical records.
      - can_delete = False: Prevents accidental deletion of individual
        messages, preserving conversation integrity.
    """
    model = ChatMessage
    extra = 0
    readonly_fields = ['sender', 'message', 'created_at']
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatSession.

    The list view shows each session's ID, phone number, linked Lead,
    and start/end times. The 'inlines' attribute embeds the
    ChatMessageInline so the full conversation appears when you click
    into a session.

    Config fields:
      - list_display: Columns shown in the changelist view.
      - list_filter:  Filter sidebar by start date.
      - search_fields: Search box for phone or lead phone.
      - inlines:      Attach ChatMessageInline to the detail view.
    """
    list_display = ['id', 'phone', 'lead', 'started_at', 'ended_at']
    list_filter = ['started_at']
    search_fields = ['phone', 'lead__phone']
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatMessage.

    In the list view, instead of showing the full message text (which
    could be very long and distort the table layout), we use a custom
    method `message_preview` that truncates long messages.

    The @admin.display(description='Message') decorator on
    message_preview customises the column header in the admin.
    """
    list_display = ['session', 'sender', 'message_preview', 'created_at']
    list_filter = ['sender']
    search_fields = ['message']

    @admin.display(description='Message')
    def message_preview(self, obj):
        """
        Return a truncated version of the message for the list view.

        obj is a ChatMessage instance. If the message is longer than
        60 characters, we show the first 60 characters followed by '...'.
        Otherwise we show the full message.

        The @admin.display decorator sets the column header text to
        'Message' instead of the method name 'message_preview'.
        """
        if len(obj.message) > 60:
            return obj.message[:60] + '...'
        return obj.message
