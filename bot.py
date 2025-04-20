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

# Owner ID
owner_id = 7063105762

# Typing simulation
async def send_typing(event, text_length=20):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    typing_time = min(5, max(1.5, text_length / 15))
    await asyncio.sleep(random.uniform(1.0, typing_time))

# Gali list
bad_words = ["bc", "bkl", "mc", "madarchod", "bhenchod", "chutiya", "lode", "loda", "gaand", "gaandfat", "gandu"]

# New System Prompt
system_prompt = """
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

Services:
- OTT: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, YouTube Premium, Telegram Premium etc.
- Adult Sites: (poora list available on request), 6 months ₹300, 1 year ₹500
- PC BGMI Hacks: Titan, Falcone, Vision, Lethal, Sharpshooter, rooted & non-rooted available
- iOS Hacks: Shoot360, WinIOS, iOSZero

Pricing:
- OTT 1 Year ₹500 (Own Email)
- OTT 6 Months ₹350 (Random Email)
- Combo 4 OTT 1 Year ₹1000
- Hack Week ₹800 / Month ₹1300
- ChatGPT Premium 1 Year ₹1000

Rules:
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

Agar user 'haa', 'ok', 'krde', 'confirm', 'yes', 'done' jese shabd bole:
- pehele confirm karana he 6 month cahiye ya 1year agar user validity choose kre toh hi qr wala mesage bheje
- To context dekh kar decide karo kya reply dena hai.
- Agar lagta hai user payment confirm kar raha hai to "QR code generate ho raha hai bhai ❤️" type ka human funny reply do.
- Agar lagta hai normal casual baat hai to bas friendly dosti bhara normal reply do.
- Hardcoded kabhi kuch na bolo, context samajh ke smart reply do.

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
"""

@client.on(events.NewMessage)
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    # AI control commands
    stop_commands = ['/stopai', 'stop ai', 'band kar de ai', 'ai band kar', 'close ai']
    start_commands = ['/startai', 'start ai', 'ai start kar', 'chalu kar ai', 'open ai']

    if any(cmd.replace(' ', '') in user_message.replace(' ', '') for cmd in stop_commands):
        if sender_id == owner_id:
            ai_active = False
            await event.respond("AI system band kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
        return

    if any(cmd.replace(' ', '') in user_message.replace(' ', '') for cmd in start_commands):
        if sender_id == owner_id:
            ai_active = True
            await event.respond("AI system chalu kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
        return

    if not ai_active:
        return

    if sender_id in muted_users:
        return

    if any(bad_word in user_message for bad_word in bad_words):
        user_warnings[sender_id] = user_warnings.get(sender_id, 0) + 1
        if user_warnings[sender_id] >= 3:
            muted_users.add(sender_id)
            await event.respond("Tumhe mute kar diya gaya hai. Aage reply nahi milega.")
        else:
            await event.respond(f"Warning {user_warnings[sender_id]}: Gali mat do.")
        return

    await send_typing(event, len(user_message))

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await send_typing(event, len(bot_reply))
        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Error aaya. Baad me try karna.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
