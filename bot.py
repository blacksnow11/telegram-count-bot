import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import TelegramError

# 🔐 HARD-CODED BOT TOKEN (paste your real token here locally)
BOT_TOKEN = "7895003356:AAHhgFRQ6tEW0_G3g_ZTnyZCVuvloDf4V6g"

# 📢 Channel username
CHANNEL_USERNAME = "@certified_escrow"

# 🔒 Only YOU are allowed to use the bot
AUTHORIZED_USERS = {8182255472}

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text("⚠️ Please use this command in a private chat with the bot.")
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

    try:
        sent = await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"{base_text}\n\n⏳ Time left: {hours:02d}:{minutes:02d}"
        )
    except TelegramError as e:
        await update.message.reply_text(f"Failed to send message to channel: {e}")
        return

    message_id = sent.message_id

    while True:
        remaining = end_time - datetime.utcnow()
        total_seconds = int(remaining.total_seconds())

        if total_seconds <= 0:
            break

        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60

        try:
            await context.bot.edit_message_text(
                chat_id=CHANNEL_USERNAME,
                message_id=message_id,
                text=f"{base_text}\n\n⏳ Time left: {h:02d}:{m:02d}:{s:02d}"
            )
        except TelegramError:
            pass  # Message might be deleted or failed

        # Sleep only 1 second for precise countdown
        await asyncio.sleep(1)

    # Final message edits
    try:
        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=message_id,
            text="⛔ Discount expired"
        )
    except TelegramError:
        pass

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
