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
user_warnings = {}
muted_users = set()
ai_active = True  # AI initially active

# Typing simulation
async def send_typing(event):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.uniform(0.8, 1.5))

# Gali list
bad_words = ["bc", "bkl", "mc", "madarchod", "bhenchod", "chutiya", "lode", "loda", "gaand", "gaandfat", "gandu"]

# System Prompt for ChatGPT-4o
system_prompt = """
Tum ek smart aur friendly OTT subscription seller ho India me.
Tum sabhi major OTT platforms ka subscription sell karte ho:

Netflix, Amazon Prime Video, Disney+ Hotstar, SonyLIV, Zee5, Voot, ALT Balaji, MX Player, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, SunNxt, Hungama Play, ShemarooMe, Lionsgate Play, ManoramaMAX, DocuBay, Epic On, Chaupal, Planet Marathi, Klikk, Addatimes, NammaFlix, Tarang Plus, Aha, TVF Play, Vi Movies & TV, YouTube Premium, Telegram Premium, ChatGPT Subscription bhi bech rahe ho.

Plans:
- 1 Year Plan = ₹500 (Own Email/Number activation, Premium Plan, Max Screen Support, 1 Year Guarantee)
- 6 Months Plan = ₹350 (Random Email Activation, OTP login, same features but random email)
- Combo Offer = Any 4 OTTs 1 Year Plan = ₹1000 (Own Email/Number Activation, Max Screens support, Premium Plans)
- ChatGPT Premium 1 Year Plan = ₹1000

Movie handling:
- Agar user kisi movie ka naam le jaise "Animal", "Dunki", "Pathaan", to batana ki yeh movie kis OTT pe available hai
- Fir friendly bolna ki "OTT buy karlo bhai, full HD dekh paoge ❤️"
PC Games:
- Agar user koi game ka naam le (e.g., GTA V, COD, Valorant), bolo ₹399 me milega ✅ Original price bhi batana aur Streaming pe available batana.

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab confirm kare (haa, krde, ok) to "QR generate ho raha hai bhai, wait karo 📲" bolo
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Jab koi gali de to 3 warning ke baad mute kar dena aur reply ignore karna
- Owner agar /stopai bole to bot band karo aur /startai pe wapas chalu karo
- Full human funny comedy style reply dena, robotic mat lagna
- tumhre pass sare adult sites ke subscreptions bhi he 6 month 300rs 1 year 500 rs or user mange toh eska pura list de sakte ho
- adult sites ka sara naam bata sakte ho pura list de skte ho 
- bgmi ka hack bhi avalable he tumhre pass hack me vision,lithal, ye dono non rooted hack he sharpshootr,titan, ye roooted hack he pc emulater bgmi hack titan or falcone he sare hacks safe he main id k liye ban hua toh refund kr dega week 800 rs or 1 month 1300 rs
- agar user koi b hack ka naam leta he toh wo tumhre pass he feeturs esp,bullet track,no recoil.esp hide ,aimbot 
- or ios ke liye bhi hack he tumpe shoot360,winios,ioszero price sab ka same he or feturs bhi 
- ye or koi help cahiye toh batao ye sare message me add krne ki zarurat nai bhat kam case me use kro
- telegram,hotstar,zee5,sony ye sab ke liye mail nai cahiye ye number pe activate hoga
"""

# Confirmation words
confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'ok', 'thik hai', 'confirm', 'yes', 'okey']

@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender_id = (await event.get_sender()).id
    user_message = event.raw_text.strip().lower()

    # Commands: /stopai /startai
    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI reply system stopped. Ab me chup rahunga jab tak /startai nahi aata 😄")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI reply system started. Ab me wapas reply karunga 😄")
        return

    # If AI inactive, don't reply
    if not ai_active:
        return

    # Muted user check
    if sender_id in muted_users:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    # Gali Detection
    if any(bad_word in user_message for bad_word in bad_words):
        user_warnings[sender_id] = user_warnings.get(sender_id, 0) + 1
        if user_warnings[sender_id] >= 3:
            muted_users.add(sender_id)
            await event.respond("⚠️ Bhai 3 warning ke baad tujhe mute kar diya gaya hai 🚫")
        else:
            await event.respond(f"⚠️ Warning {user_warnings[sender_id]}: Gali mat de bhai 🙏")
        return

    try:
        # Handle direct confirms (only exact words)
        if user_message.strip() in confirm_words:
            await event.respond("Sahi decision bhai ✅ QR generate ho raha hai 📲 Wait karna thoda 😎")
            return

        # Thanks
        if user_message in ['thank', 'thanks', 'thank you', 'shukriya', 'dhanyawaad']:
            await event.respond("Welcome bhai 😄 Hamesha ready hoon madad ke liye!")
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
