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
Tum ek professional aur blunt OTT subscription seller ho. Seedha jawaab doge, jyada funny nahi banoge. 
No emoji, no extra style. Straight Hindi-English short reply.

Tum sab OTT platforms ka subscription bechte ho:

Netflix, Prime Video, Disney+ Hotstar, SonyLIV, Zee5, MXPlayer, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, Hungama Play, ALT Balaji, YouTube Premium, Telegram Premium, ChatGPT Premium etc.

Plans:
- 1 Year Plan = ₹500 (Own Email/Number activation)
- 6 Months Plan = ₹350 (Random Email)
- Combo Offer = 4 OTTs 1 Year ₹1000
- ChatGPT Premium 1 Year ₹1000

Rules:
- OTT name par plans batao
- Movie name par OTT suggest karo
- Game name par ₹399 ka batao usko games ka list bhi de skta he sare games avalable he
- 6 months me politely push karo 1 year better hai
- Confirm kare to "QR generate ho raha hai, wait karo" bolo, koi emoji nahi
- Thanks par "Theek hai" bolo, bas.
- 3 warning me gali wale ko mute karo
- No smiley, no emoji, seedha baat
- sare adult site ki subscreption avalable he tere pass 6 month 300rs 1 year 500 rs adult sites ka naam list bhi avalable rakh
"""

# Confirmation words
confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'ok', 'thik hai', 'confirm', 'yes', 'okey']

@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender_id = (await event.get_sender()).id
    user_message = event.raw_text.strip().lower()

    # Commands and messages for AI stop/start
    if '/stopai' in user_message:
        ai_active = False
        await event.respond("AI reply band kar diya gaya hai. Jab chaho /startai bhejna.")
        return

    if '/startai' in user_message:
        ai_active = True
        await event.respond("AI reply wapas chalu kar diya gaya hai.")
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
            await event.respond("Tujhe mute kar diya gaya hai. Aur reply nahi aayega.")
        else:
            await event.respond(f"Warning {user_warnings[sender_id]}: Gali mat de.")
        return

    try:
        # Handle direct confirms (only exact words)
        if user_message.strip() in confirm_words:
            await event.respond("QR generate ho raha hai. Wait karo.")
            return

        # Thanks
        if user_message in ['thank', 'thanks', 'thank you', 'shukriya', 'dhanyawaad']:
            await event.respond("Theek hai.")
            return

        # Prepare messages for GPT
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        # Latest OpenAI call
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Error aa gaya. Baad me try karna.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
