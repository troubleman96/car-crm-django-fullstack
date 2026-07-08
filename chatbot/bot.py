"""
chatbot/bot.py — Automated chatbot reply engine.

This is the "brain" of the chatbot. It takes a user's message as input
and returns an appropriate reply using keyword matching (no AI/LLM).

====================================================================
              HOW THE KEYWORD MATCHING ALGORITHM WORKS
====================================================================

  1. The incoming message is converted to lowercase and stripped of
     leading/trailing whitespace (normalisation).

  2. A series of if/elif checks each calls re.search() with a regex
     pattern that looks for specific keywords in the message.

  3. The FIRST pattern to match wins — the order of checks is
     important! Greetings are checked first, then price questions,
     then car makes, etc. This means a message containing both a
     greeting and a car brand (e.g., "Hello, tell me about Toyota")
     will get the GREETING reply, not the Toyota reply.

  4. If NO keyword pattern matches, a generic fallback response
     is returned.

  NOTE ON SWAHILI SUPPORT:
    This chatbot is designed for a Tanzanian dealership, so it
    recognises several Swahili words alongside English ones:
      - habari / mambo / jambo   (greetings — "how are you / what's up")
      - bei / gharama            (price — "price / cost")
      - asante                   (thank you)
      - sawa                     (okay / thanks)
      - saida                    (help — "help / assist")
    These are included in the same regex patterns as their English
    equivalents, so a user can mix languages freely.

  NOTE ON re (REGULAR EXPRESSIONS):
    The `re` module provides pattern matching in strings.
    - re.search(pattern, text) returns a Match object if the pattern
      is found ANYWHERE in the text, or None otherwise.
    - \\b is a word-boundary anchor — it ensures the keyword is a
      whole word, not part of a larger word (e.g., "\\btoyota\\b"
      matches "I want a Toyota" but NOT "toyotathon").
    - The pipe | means OR inside a character group or group.
    - re.IGNORECASE could be used, but we already handle case by
      calling message.lower() before matching.

====================================================================
"""

import re


def get_bot_reply(message: str) -> str:
    """
    Generate a chatbot reply based on keyword matching.

    Args:
        message: The raw message string from the website visitor.

    Returns:
        A response string that the chatbot will send back.

    Type hint: `message: str` and `-> str` indicate that this function
    takes a string and returns a string. These hints are optional in
    Python but help with code clarity and IDE autocompletion.
    """

    # ------------------------------------------------------------------
    # Normalise the input: convert to lowercase and strip whitespace.
    #
    # Lowercasing ensures our keyword matching is case-insensitive:
    # "Hello", "hello", and "HELLO" all match the same pattern.
    #
    # .strip() removes accidental spaces the user might type.
    # ------------------------------------------------------------------
    msg = message.lower().strip()

    # ------------------------------------------------------------------
    # CHECK 1: Greetings (English + Swahili)
    #
    # Pattern: \\b(hi|hello|hey|habari|mambo|jambo)\\b
    #
    # If the user says any of these words, we assume they're starting
    # a conversation and respond with a friendly welcome message
    # that invites further questions.
    #
    # Swahili words:
    #   habari = "news" / "how are you?"
    #   mambo  = slang for "what's up?"
    #   jambo  = formal greeting
    # ------------------------------------------------------------------
    greetings = re.search(r'\b(hi|hello|hey|habari|mambo|jambo)\b', msg)
    if greetings:
        return "Hello! Welcome to our dealership. How can I help you today? You can ask about our cars, prices, or book a test drive."

    # ------------------------------------------------------------------
    # CHECK 2: Price / cost queries
    #
    # Pattern: \\b(price|cost|how much|bei|gharama)\\b
    #
    # "how much" is a multi-word pattern — re.search handles this
    # fine because the whole string \\bhow much\\b is treated as a
    # literal phrase within the alternation group.
    #
    # Swahili:
    #   bei     = price
    #   gharama = cost / expense
    # ------------------------------------------------------------------
    if re.search(r'\b(price|cost|how much|bei|gharama)\b', msg):
        return "We have a range of cars available at different prices. Could you let me know which make or model you're interested in? I can share the details."

    # ------------------------------------------------------------------
    # CHECK 3: Specific car makes / brands
    #
    # Pattern: \\b(toyota|nissan|bmw|mercedes|honda|suzuki|mitsubishi|hyundai)\\b
    #
    # If the user mentions any car brand, we capture which one they
    # said using .group(1), capitalise it with .capitalize(), and
    # use it in the response. This makes the reply feel personalised.
    #
    # Note: The re.search() is run TWICE here — first in the if
    # condition, then inside the block to extract the matched brand.
    # This is slightly wasteful but keeps the code simple. An
    # alternative would be to assign it to a variable in the if:
    #   match = re.search(...)
    #   if match: ...
    # ------------------------------------------------------------------
    if re.search(r'\b(toyota|nissan|bmw|mercedes|honda|suzuki|mitsubishi|hyundai)\b', msg):
        car_make = re.search(r'\b(toyota|nissan|bmw|mercedes|honda|suzuki|mitsubishi|hyundai)\b', msg).group(1)
        return f"Great choice! We have several {car_make.capitalize()} models available. Would you like to book a test drive or visit our showroom?"

    # ------------------------------------------------------------------
    # CHECK 4: Test drive requests
    #
    # Pattern: \\b(test drive|test|drive|trial)\\b
    #
    # Matches phrases like "I want a test drive", "can I test it",
    # "drive the car", etc. Note: "test" alone is broad (could match
    # "test the engine"), but for a car dealership chatbot this is
    # almost always about test driving.
    # ------------------------------------------------------------------
    if re.search(r'\b(test drive|test|drive|trial)\b', msg):
        return "You can book a test drive right here! Just click the 'Book a Test Drive' button on our website, or tell me your preferred date and time, and I'll help set it up."

    # ------------------------------------------------------------------
    # CHECK 5: Booking / appointment / scheduling
    #
    # Pattern: \\b(book|appointment|schedule|reserve|order)\\b
    #
    # These keywords indicate the user wants to arrange something.
    # The response asks clarifying questions to determine what kind
    # of appointment they need, and asks for their phone number.
    # ------------------------------------------------------------------
    if re.search(r'\b(book|appointment|schedule|reserve|order)\b', msg):
        return "I'd be happy to help you book an appointment! Would you like a test drive, a call back from our sales team, or a showroom visit? Please share your phone number and I'll get you scheduled."

    # ------------------------------------------------------------------
    # CHECK 6: Contact / phone / call requests
    #
    # Pattern: \\b(phone|call|contact|reach|whatsapp)\\b
    #
    # The user wants to speak to a human. We give them the dealership
    # phone number and suggest they share their number for a call-back.
    # ------------------------------------------------------------------
    if re.search(r'\b(phone|call|contact|reach|whatsapp)\b', msg):
        return "You can reach our sales team by calling +255712345678 or visiting our showroom. If you share your phone number, I can have a team member call you back."

    # ------------------------------------------------------------------
    # CHECK 7: Location / showroom / address
    #
    # Pattern: \\b(location|showroom|where|address|shop)\\b
    #
    # The user wants to visit. We mention Dar es Salaam as the location
    # and offer to help with directions or scheduling.
    # ------------------------------------------------------------------
    if re.search(r'\b(location|showroom|where|address|shop)\b', msg):
        return "Our showroom is located in Dar es Salaam, Tanzania. Would you like directions or would you like to schedule a visit?"

    # ------------------------------------------------------------------
    # CHECK 8: Thanks / gratitude (English + Swahili)
    #
    # Pattern: \\b(thank|thanks|asante|sawa)\\b
    #
    # Swahili:
    #   asante = thank you
    #   sawa   = okay / alright (often used to acknowledge)
    #
    # When the user thanks us, we reply politely and keep the
    # conversation open for further questions.
    # ------------------------------------------------------------------
    if re.search(r'\b(thank|thanks|asante|sawa)\b', msg):
        return "You're welcome! Feel free to ask if you have any other questions. We're here to help you find the perfect car."

    # ------------------------------------------------------------------
    # CHECK 9: Help / support requests (English + Swahili)
    #
    # Pattern: \\b(help|support|assist|saida)\\b
    #
    # Swahili:
    #   saida = help
    #
    # If the user is asking for help generally, we list the things
    # the bot can help with.
    # ------------------------------------------------------------------
    if re.search(r'\b(help|support|assist|saida)\b', msg):
        return "I'm here to help! You can ask about our car inventory, pricing, booking a test drive, or our location. What would you like to know?"

    # ------------------------------------------------------------------
    # FALLBACK: No keywords matched
    #
    # If none of the above patterns matched, we return a generic,
    # friendly message that keeps the conversation going and invites
    # the user to provide more information (especially a phone number
    # for a human to follow up).
    #
    # In a production system, this would be a good place to hand off
    # to a human agent or log the unmatched message for analysis.
    # ------------------------------------------------------------------
    return "Thank you for your message! I'd be happy to help you find the right car. Would you like to book a test drive or speak with our sales team? Just let me know your phone number and I'll connect you."
