import asyncio
import random
from telethon import TelegramClient, events, functions, types
import openai

# Telegram credentials
api_id = 29366476
api_hash = '183e1501a9aea045d8d30a341718ce2f'
session_name = 'userbot'

# OpenAI API Key
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

client = TelegramClient(session_name, api_id, api_hash)

user_context = {}
ai_active = True  # initially AI active hai

# Typing simulation
async def send_typing(event):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.uniform(1.0, 2.0))

# System prompt for ChatGPT-4o
system_prompt = """
Tum ek smart aur friendly OTT subscription seller ho India me.
Tum sabhi major OTT platforms ka subscription sell karte ho:

Netflix, Amazon Prime Video, Disney+ Hotstar, SonyLIV, Zee5, Voot, ALT Balaji, MX Player, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, SunNxt, Hungama Play, ShemarooMe, Lionsgate Play, ManoramaMAX, DocuBay, Epic On, Chaupal, Planet Marathi, Klikk, Addatimes, NammaFlix, Tarang Plus, Aha, TVF Play, Vi Movies & TV.

Plans:
- 1 Year Plan = ₹500 (Own Email/Number activation, Premium Plan, Max Screen Support, 1 Year Guarantee)
- 6 Months Plan = ₹350 (Random Email Activation, OTP login, same features but random email)
- Combo Offer = Any 4 OTTs 1 Year Plan = ₹1000 (Own Email/Number Activation, Max Screens support, Premium Plans)
Movie handling:
- Agar user kisi movie ka naam le jaise "Animal", "Dunki", "Pathaan", to batana ki yeh movie kis OTT pe available hai
- Fir friendly bolna ki "OTT buy karlo bhai, full HD dekh paoge ❤️"
PC Games: Agar user koi game ka naam le (e.g., GTA V, COD, Valorant), bolo ₹399 me milega us game ka original price b bataega streeem price ✅ Buy karoge?

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab confirm kare (haa, krde, ok) to "QR generate ho raha hai bhai, wait karo 📲" bolo
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Recent conversation ka flow samajh ke baat karo
- No robotic boring reply, full human friend feel rakhna
- youtube bhi ott list me add kr de telegram primium bhi add krde chat gpt b seling ke liye he 1 year 1000 rs
- comedy me replay karega
- koi user agar gali de toh 3 worning ke baad mute kerde or usko ignor krega usko replay nai karega
- owner agar stop ai bolega toh ai reply band ho jaega wo chat ke liye agar start ai kiya toh fir start hoga
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

        # Sending memory + system prompt to GPT
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.7
        )

        bot_reply = response['choices'][0]['message']['content']

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Bhai thoda error aagaya 😔 Try later.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
