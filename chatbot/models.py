"""
chatbot/models.py — Database models for the Chatbot app.

This app stores chat conversations between website visitors and the
automated chatbot (or a human agent). There are two models:

  - ChatSession: Represents one conversation "session" — it starts
    when a visitor sends their first message and optionally ends
    when the conversation is marked complete.

  - ChatMessage: An individual message within a session. Every message
    has a sender type (customer, bot, or agent) and the message text.

These models work together with chatbot/views.py (the JSON API) and
chatbot/bot.py (the keyword-matching reply engine).
"""

from django.db import models


class ChatSession(models.Model):
    """
    Represents a single chat conversation session.

    When a visitor opens the chat widget and sends their first message,
    a ChatSession is created. All subsequent messages in that conversation
    are linked to this session via a ForeignKey on ChatMessage.

    Key concepts:
      - lead:  If the visitor provides a phone number, we try to link
               this session to an existing Lead (or create a new one).
               This is how chat conversations become sales leads.
               SET_NULL means the session survives even if the Lead is
               deleted (the field just becomes NULL).
      - phone: The visitor's phone number (if provided). Stored directly
               on the session for quick access, even if no Lead exists yet.

    Relationship to leads:
      - When a visitor says something like "Book a test drive" AND gives
        a phone number, the chatbot view (chatbot/views.py) creates a
        Lead record via Lead.objects.get_or_create() and attaches it
        to this session via session.lead = lead.
    """
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    # phone is stored directly on the session so we can identify returning
    # visitors even before a Lead is created. Nullable because the visitor
    # might start a chat without providing a phone number.
    phone = models.CharField(max_length=15, null=True, blank=True)

    # auto_now_add=True: Automatically records the timestamp when the
    # session row is first INSERTed into the database.
    started_at = models.DateTimeField(auto_now_add=True)

    # ended_at: Null until the session is explicitly ended (e.g., by an
    # admin closing it or after a timeout). Nullable because open sessions
    # don't have an end time yet.
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """
        Human-readable representation for the admin panel and shell.

        If no phone is available, falls back to "Anonymous".
        """
        return f'Session {self.id} - {self.phone or "Anonymous"}'


class ChatMessage(models.Model):
    """
    Represents one message in a chat session.

    Each message is:
      - Linked to exactly one ChatSession (via ForeignKey).
      - Tagged with who sent it (customer, bot, or agent).
      - Stored as plain text.

    The ordering Meta makes sure messages are returned in chronological
    order when queried (e.g., session.messages.all()).
    """

    # --- SENDER_CHOICES ---
    # The 'choices' pattern again — values stored in the DB are the
    # short codes ('customer', 'bot', 'agent'), but Django will show
    # the readable labels ('Customer', 'Bot', 'Agent') in the admin.
    SENDER_CHOICES = [
        ('customer', 'Customer'),  # Sent by the website visitor
        ('bot', 'Bot'),            # Automated reply from bot.py
        ('agent', 'Agent'),        # Manual reply from a human sales agent
    ]

    # ForeignKey to ChatSession with CASCADE delete: deleting a session
    # deletes all its messages. related_name='messages' creates the
    # reverse relation: session.messages.all() gives all messages in
    # a session.
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    # sender: Who wrote this message. Limited to the choices above.
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)

    # message: The actual text content. TextField (unlike CharField)
    # has no maximum length limit, so long conversations are fine.
    message = models.TextField()

    # Automatically timestamped when the message is created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Messages are ordered oldest-first (chronological).
        # This is important for displaying the chat history correctly.
        ordering = ['created_at']

    def __str__(self):
        """
        Show the sender label and the first 50 characters of the message.

        The slice [:50] prevents the string representation from being
        too long in the admin list view.
        """
        return f'[{self.sender}] {self.message[:50]}'
