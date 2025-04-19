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
owner_id = 7063105762  # <-- Tera Owner ID set kar diya hai

# Typing simulation
async def send_typing(event):
    await event.client(functions.messages.SetTypingRequest(
        peer=event.chat_id,
        action=types.SendMessageTypingAction()
    ))
    await asyncio.sleep(random.uniform(0.8, 1.5))

# Gali list
bad_words = ["bc", "bkl", "mc", "madarchod", "bhenchod", "chutiya", "lode", "loda", "gaand", "gaandfat", "gandu"]

# Stop/Start command list
stop_commands = ['/stopai', 'stop ai', 'band kar de ai', 'ai band kar', 'band kar ai', 'close ai']
start_commands = ['/startai', 'start ai', 'ai start kar', 'chalu kar ai', 'open ai', 'ai chalu kar']

# System Prompt for GPT
system_prompt = """
Tum ek professional aur blunt OTT subscription seller ho. Seedha jawaab doge, jyada funny nahi banoge. 
No emoji, no extra style. Straight Hindi-English short reply.

OTT List: Netflix, Prime Video, Disney+ Hotstar, SonyLIV, Zee5, MXPlayer, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, Hungama Play, ALT Balaji, YouTube Premium, Telegram Premium, ChatGPT Premium etc.

Plans:
- 1 Year = ₹500 (Own Email Activation)
- 6 Months = ₹350 (Random Email)
- Combo 4 OTT = ₹1000
- ChatGPT 1 Year = ₹1000

Reply seedha, clear, no emoji, no jokes.
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'ok', 'thik hai', 'confirm', 'yes', 'okey']

@client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()
    user_message_clean = user_message.replace(' ', '')

    # Commands for AI control
    if any(cmd.replace(' ', '') in user_message_clean for cmd in stop_commands):
        if sender_id == owner_id:
            ai_active = False
            await event.respond("AI reply system band kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
        return

    if any(cmd.replace(' ', '') in user_message_clean for cmd in start_commands):
        if sender_id == owner_id:
            ai_active = True
            await event.respond("AI reply system chalu kar diya gaya hai.")
        else:
            await event.respond("Ye command sirf owner ke liye hai.")
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
            await event.respond("Tujhe mute kar diya gaya hai. Aage reply nahi milega.")
        else:
            await event.respond(f"Warning {user_warnings[sender_id]}: Gali mat de.")
        return

    try:
        # Handle direct confirms (only exact word)
        if user_message.strip() in confirm_words:
            await event.respond("QR generate ho raha hai. Wait karo.")
            return

        # Thanks reply
        if user_message in ['thank', 'thanks', 'thank you', 'shukriya', 'dhanyawaad']:
            await event.respond("Theek hai.")
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

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Error aa gaya. Baad me try karna.")
        print(f"Error: {e}")

client.start()
client.run_until_disconnected()
