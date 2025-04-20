import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai

# --- Railway Environment Variables Se Uthana ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = 'newuserbot'

# OpenAI Client Initialization (NEW WAY)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Group ID
GROUP_ID = -1002470019043

telegram_client = TelegramClient(session_name, api_id, api_hash)

# Memory
user_context = {}
user_confirm_pending = {}
group_msg_to_user = {}

ai_active = True

# Typing simulation
async def send_typing(event):
    try:
        await event.client(functions.messages.SetTypingRequest(
            peer=event.chat_id,
            action=types.SendMessageTypingAction()
        ))
        await asyncio.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"Typing error: {e}")

# Always online
async def keep_online():
    while True:
        try:
            await telegram_client(functions.account.UpdateStatusRequest(offline=False))
        except Exception as e:
            print(f"Online error: {e}")
        await asyncio.sleep(60)

# System Prompt
system_prompt = """
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

Plans:
- OTT 1 Year ₹500 (Own Email)
- OTT 6 Months ₹350 (Random Email)
- Combo 4 OTTs ₹1000
- ChatGPT Premium 1 Year ₹1000

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab thank you bole to friendly short welcome bolo
- Jab user confirm kare to payment post karo
- Full human funny comedy style reply dena
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'paid', 'payment ho gaya', 'payment done', 'payment hogaya']

@telegram_client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI reply system stopped.")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI reply system started.")
        return

    if not ai_active:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        # Plan Selection
        if "6 month" in user_message or "6 months" in user_message:
            user_confirm_pending[sender_id] = {
                "validity": "6 Months",
                "subscription_name": "OTT Subscription",
                "price": "₹350"
            }
            await event.respond("✅ 6 Months plan selected. Confirm karo bhai.")
            return

        if "1 year" in user_message or "12 months" in user_message:
            user_confirm_pending[sender_id] = {
                "validity": "1 Year",
                "subscription_name": "OTT Subscription",
                "price": "₹500"
            }
            await event.respond("✅ 1 Year plan selected. Confirm karo bhai.")
            return

        # User confirms
        if any(word in user_message for word in confirm_words):
            if sender_id in user_confirm_pending:
                plan = user_confirm_pending[sender_id]
                subscription_name = plan['subscription_name']
                validity = plan['validity']
                payment_amount = plan['price']

                user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

                post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
💰 Amount: {payment_amount}
🎯 Subscription: {subscription_name}
⏳ Validity: {validity}
"""
                post = await telegram_client.send_message(
                    GROUP_ID,
                    post_text,
                    parse_mode='html'
                )

                group_msg_to_user[post.id] = sender_id
                del user_confirm_pending[sender_id]

                await event.respond("✅ Sahi decision bhai! QR generate ho raha hai 📲 Wait karo 😎")
                return
            else:
                await event.respond("✅ Bhai payment screenshot bhejo!")
                return

        # Screenshot Handling
        if event.photo or (event.document and "image" in event.file.mime_type):
            await telegram_client.send_message(
                GROUP_ID,
                f"✅ Payment Screenshot from {sender.first_name} ({sender_id})"
            )
            await telegram_client.forward_messages(
                GROUP_ID,
                event.message,
                event.chat_id
            )
            await event.respond("✅ Screenshot mil gaya bhai! Check ho raha hai.")
            return

        # Normal ChatGPT conversation
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        # NEW OpenAI call
        response = client.chat.completions.create(
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

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.run_until_disconnected()
