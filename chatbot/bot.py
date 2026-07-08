import re


def get_bot_reply(message: str) -> str:
    msg = message.lower().strip()

    greetings = re.search(r'\b(hi|hello|hey|habari|mambo|jambo)\b', msg)
    if greetings:
        return "Hello! Welcome to our dealership. How can I help you today? You can ask about our cars, prices, or book a test drive."

    if re.search(r'\b(price|cost|how much|bei|gharama)\b', msg):
        return "We have a range of cars available at different prices. Could you let me know which make or model you're interested in? I can share the details."

    if re.search(r'\b(toyota|nissan|bmw|mercedes|honda|suzuki|mitsubishi|hyundai)\b', msg):
        car_make = re.search(r'\b(toyota|nissan|bmw|mercedes|honda|suzuki|mitsubishi|hyundai)\b', msg).group(1)
        return f"Great choice! We have several {car_make.capitalize()} models available. Would you like to book a test drive or visit our showroom?"

    if re.search(r'\b(test drive|test|drive|trial)\b', msg):
        return "You can book a test drive right here! Just click the 'Book a Test Drive' button on our website, or tell me your preferred date and time, and I'll help set it up."

    if re.search(r'\b(book|appointment|schedule|reserve|order)\b', msg):
        return "I'd be happy to help you book an appointment! Would you like a test drive, a call back from our sales team, or a showroom visit? Please share your phone number and I'll get you scheduled."

    if re.search(r'\b(phone|call|contact|reach|whatsapp)\b', msg):
        return "You can reach our sales team by calling +255712345678 or visiting our showroom. If you share your phone number, I can have a team member call you back."

    if re.search(r'\b(location|showroom|where|address|shop)\b', msg):
        return "Our showroom is located in Dar es Salaam, Tanzania. Would you like directions or would you like to schedule a visit?"

    if re.search(r'\b(thank|thanks|asante|sawa)\b', msg):
        return "You're welcome! Feel free to ask if you have any other questions. We're here to help you find the perfect car."

    if re.search(r'\b(help|support|assist|saida)\b', msg):
        return "I'm here to help! You can ask about our car inventory, pricing, booking a test drive, or our location. What would you like to know?"

    return "Thank you for your message! I'd be happy to help you find the right car. Would you like to book a test drive or speak with our sales team? Just let me know your phone number and I'll connect you."
