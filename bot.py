import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai

# Telegram setup
api_id = 29366476
api_hash = '183e1501a9aea045d8d30a341718ce2f'
session_name = 'userbot'

client = TelegramClient(session_name, api_id, api_hash)

# OpenAI setup
openai_client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

user_context = {}
ai_active = True  # AI initially active

# Typing simulation
async def send_typing(event):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.uniform(1.0, 2.0))

# System Prompt for ChatGPT-4o
system_prompt = """
Tum ek smart aur friendly OTT + Movie + PC Game seller ho India me.
Tum following services bechte ho:

- OTT Subscriptions: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, Voot, MXPlayer, Hoichoi, Ullu, ShemarooMe, Discovery+, JioCinema, Hungama Play, ALT Balaji, etc.
- Plans: 1 Year ₹500 (Own Email), 6 Months ₹350 (Random Email)
- Combo Offer: Any 4 OTTs 1 Year ₹1000 (Own Email/Max Screens)
- Movies: Agar user movie ka naam le (e.g., Animal, Pathaan), suggest karo kis OTT pe available hai aur OTT buy karne ko encourage karo
- PC Games: Agar user koi game ka naam le (e.g., GTA V, COD, Valorant), bolo ₹399 me milega ✅ Buy karoge?

Rules:
- Hinglish me short (2-3 line) friendly reply do
- Jab user confirm kare (haa, krde, ok), bolo: "QR generate ho raha hai bhai 📲 Wait karo"
- Jab user thanks bole, sweet friendly welcome bolo
- Chat ka context yaad rakho, same cheez repeat mat karo
- Full human friend jaise feel dena, no boring robotic reply
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'ok', 'thik hai', 'confirm', 'yes', 'okey']

@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender_id = (await event.get_sender()).id
    user_message = event.raw_text.strip().lower()

    # Commands: /stopai /startai
    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI reply system stopped. Ab me chup rahunga jab tak wapas /startai nahi aata 😄")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI reply system started. Ab me wapas reply karunga 😄")
        return

    # If AI inactive, don't reply
    if not ai_active:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        # Handle direct confirms (haa, krde etc)
        if any(word in user_message for word in confirm_words):
            await event.respond("Sahi decision bhai ✅ QR generate ho raha hai 📲 Wait karna thoda 😎")
            return

        # Thanks
        if any(word in user_message for word in ['thank', 'thanks', 'thank you', 'shukriya']):
            await event.respond("Welcome bhai 😄 Always ready to help 🔥")
            return

        # Prepare messages for GPT
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        # Latest OpenAI call
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.7
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Bhai thoda error aagaya 😔 Try later.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
