import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# 🔐 HARD-CODED BOT TOKEN (paste your real token here locally)
BOT_TOKEN = "7895003356:AAHhgFRQ6tEW0_G3g_ZTnyZCVuvloDf4V6g"

# 📢 Channel username
CHANNEL_USERNAME = "@certified_escrow"

# 🔒 Only YOU are allowed to use the bot
AUTHORIZED_USERS = {8182255472}

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔐 Authorization check
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return

    # Only accept private messages
    if update.effective_chat.type != "private":
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/countdown HH:MM Your message text"
        )
        return

    time_str = context.args[0]
    base_text = " ".join(context.args[1:])

    try:
        hours, minutes = map(int, time_str.split(":"))
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM")
        return

    end_time = datetime.utcnow() + timedelta(hours=hours, minutes=minutes)

    # Initial message to channel
    sent = await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=f"{base_text}\n\n⏳ Time left: {hours:02d}:{minutes:02d}"
    )

    message_id = sent.message_id

    # Countdown loop (updates every minute)
    while True:
        await asyncio.sleep(60)

        remaining = end_time - datetime.utcnow()
        total_minutes = int(remaining.total_seconds() // 60)

        if total_minutes <= 0:
            break

        h = total_minutes // 60
        m = total_minutes % 60

        try:
            await context.bot.edit_message_text(
                chat_id=CHANNEL_USERNAME,
                message_id=message_id,
                text=f"{base_text}\n\n⏳ Time left: {h:02d}:{m:02d}"
            )
        except:
            pass  # message deleted or edit failed

    # Final edit of the original countdown message
    await context.bot.edit_message_text(
        chat_id=CHANNEL_USERNAME,
        message_id=message_id,
        text="⛔ Discount expired"
    )

    # Send a NEW message announcing expiration
    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=f"🚫 {base_text} has officially expired."
    )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("countdown", countdown))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
