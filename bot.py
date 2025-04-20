import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai

# Telegram credentials
api_id = 29366476
api_hash = '183e1501a9aea045d8d30a341718ce2f'
session_name = 'newuserbot'

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
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
- Smartly plan and price suggest karo.
- Confirm ke baad payment post karo.
- Funny, human friendly style me reply karo.
- Jab user plan final kare tabhi payment group me post karna.
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

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
- agar costmore zyada force kre toh 50 rs ka discount de dena
- 

Rules:
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Jab koi gali de to 3 warning ke baad mute kar dena aur reply ignore karna
- Owner agar /stopai bole to bot band karo aur /startai pe wapas chalu karo
- Full human funny comedy style reply dena, robotic mat lagna
- agar user bole ki usko koi or language me baat karna he toh usse age ki baat usilanguage me krna jab tak wo language chnge karne ko na bolea
- user ko bore bilkul nai krna aram se usko full convice krna ki wo buy kare
- jab ott ka price bata rahe ho us time 1 smart comparision dedo official price or hamare price me 
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'paid', 'payment ho gaya', 'payment done', 'payment hogaya']

@telegram_client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    # Handle group QR reply
    if event.is_group and event.chat_id == GROUP_ID:
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg.id in group_msg_to_user:
                user_id = group_msg_to_user[reply_msg.id]
                try:
                    await telegram_client.send_message(
                        user_id,
                        "✅ Yeh tumhara payment QR code hai bhai! Paytm / PhonePe / GPay se payment kar aur screenshot bhejna 📲"
                    )
                    if reply_msg.photo or (reply_msg.document and "image" in reply_msg.file.mime_type):
                        # ✅ Download QR from reply_msg
                        file_path = await reply_msg.download_media()
                        await telegram_client.send_file(
                            user_id,
                            file_path,
                            caption="🧾 QR Code for Payment"
                        )
                        os.remove(file_path)  # Delete temp file after sending
                    else:
                        await telegram_client.forward_messages(
                            user_id,
                            reply_msg.id,
                            GROUP_ID
                        )
                except Exception as e:
                    print(f"QR Forward Error: {e}")
        return

    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI reply system stopped. Jab tak /startai nahi karega main chup rahunga 😄")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI reply system started. Wapas reply karunga 😄")
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
            await event.respond("✅ 6 Months plan selected. Confirm karo bhai (haa/ok/krde).")
            return

        if "1 year" in user_message or "12 months" in user_message:
            user_confirm_pending[sender_id] = {
                "validity": "1 Year",
                "subscription_name": "OTT Subscription",
                "price": "₹500"
            }
            await event.respond("✅ 1 Year plan selected. Confirm karo bhai (haa/ok/krde).")
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

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.run_until_disconnected()
