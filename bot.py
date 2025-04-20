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

# Typing simulation based on text length
async def send_typing(event, text_length=20):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    typing_time = min(5, max(1.5, text_length / 15))  # Max 5 seconds, min 1.5 seconds
    await asyncio.sleep(random.uniform(1.0, typing_time))

# Gali list
bad_words = ["bc", "bkl", "mc", "madarchod", "bhenchod", "chutiya", "lode", "loda", "gaand", "gaandfat", "gandu"]

# System Prompt
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
- Confirm hone ke baad hi QR payment message bhejna
- Agar user 2+ OTT bole to combo offer suggest karna
- Gali dene par 3 warning ke baad mute kar dena
- Short aur professional Hinglish reply dena
- No emoji, straight answer
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
- uper ke message ke hisab se qr wala message do har ok,haa,ha ka qr message nai dena jab user confirm ho jae lene ke liye sab qr wala message do
- tere pass sare ott he india me jo jo avalable he
"""

# Confirmation words
confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'thik hai', 'confirm', 'yes', 'okey']

# Combo related OTTs
ott_list = ['netflix', 'prime', 'hotstar', 'sony', 'zee5', 'voot', 'mxplayer', 'ullu', 'hoichoi', 'eros', 'jio', 'discovery', 'shemaroo', 'alt', 'sun', 'aha', 'youtube', 'telegram']

@client.on(events.NewMessage)
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()
    user_message_clean = user_message.replace(' ', '')

    # AI control by Owner
    stop_commands = ['/stopai', 'stop ai', 'band kar de ai', 'ai band kar', 'close ai']
    start_commands = ['/startai', 'start ai', 'ai start kar', 'chalu kar ai', 'open ai']

    if any(cmd.replace(' ', '') in user_message_clean for cmd in stop_commands):
        if sender_id == owner_id:
            ai_active = False
            await event.respond("AI system band kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
        return

    if any(cmd.replace(' ', '') in user_message_clean for cmd in start_commands):
        if sender_id == owner_id:
            ai_active = True
            await event.respond("AI system chalu kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
        return

    # If AI inactive, don't reply
    if not ai_active:
        return

    # Muted users no reply
    if sender_id in muted_users:
        return

    # Gali detection
    if any(bad_word in user_message for bad_word in bad_words):
        user_warnings[sender_id] = user_warnings.get(sender_id, 0) + 1
        if user_warnings[sender_id] >= 3:
            muted_users.add(sender_id)
            await event.respond("Tumhe mute kar diya gaya hai. Aage reply nahi milega.")
        else:
            await event.respond(f"Warning {user_warnings[sender_id]}: Gali mat do.")
        return

    # Start typing simulation based on user input length
    await send_typing(event, len(user_message))

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        # Handle smart confirms
        if user_message.strip() in confirm_words:
            await event.respond("QR code generate ho raha hai. Thoda wait karo.")
            return

        # Thanks
        if user_message in ['thank', 'thanks', 'thank you', 'shukriya', 'dhanyawaad']:
            await event.respond("Theek hai.")
            return

        # Auto Combo Suggestion
        ott_matches = [ott for ott in ott_list if ott in user_message]
        if len(ott_matches) >= 2:
            await event.respond("Bhai combo offer le lo 4 OTT 1 saath ₹1000 me. 1 year validity ke saath.")
            return

        # Prepare GPT-4o prompt
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        # Typing simulation for bot reply
        await send_typing(event, len(bot_reply))

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Error aaya. Baad me try karna.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
