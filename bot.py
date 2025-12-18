import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import TelegramError

# 🔐 Paste your bot token here
BOT_TOKEN = "7895003356:AAHhgFRQ6tEW0_G3g_ZTnyZCVuvloDf4V6g"

# 📢 Channel username
CHANNEL_USERNAME = "@certified_escrow"

# 🔒 Only authorized users
AUTHORIZED_USERS = {8182255472}

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Authorization check
    if user_id not in AUTHORIZED_USERS:
        await safe_reply(update, "🚫 You are not authorized to use this bot.")
        return

    # Must be private chat
    if update.effective_chat.type != "private":
        await safe_reply(update, "⚠️ Please use this command in a private chat with the bot.")
        return

    # Validate command arguments
    if len(context.args) < 2:
        await safe_reply(update, "Usage:\n/countdown HH:MM Your message text")
        return

    time_str = context.args[0]
    base_text = " ".join(context.args[1:])

    try:
        hours, minutes = map(int, time_str.split(":"))
        if hours < 0 or minutes < 0 or minutes >= 60:
            raise ValueError
    except ValueError:
        await safe_reply(update, "❌ Invalid time format. Use HH:MM with valid numbers.")
        return

    end_time = datetime.utcnow() + timedelta(hours=hours, minutes=minutes)

    # Send initial message to channel
    try:
        sent_message = await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"{base_text}\n\n⏳ Time left: {hours:02d}:{minutes:02d}:00"
        )
        message_id = sent_message.message_id
    except TelegramError as e:
        await safe_reply(update, f"❌ Failed to send message to the channel: {e}")
        return

    # Countdown loop
    try:
        while True:
            remaining = end_time - datetime.utcnow()
            total_seconds = int(remaining.total_seconds())

            if total_seconds <= 0:
                break

            h, remainder = divmod(total_seconds, 3600)
            m, s = divmod(remainder, 60)

            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_USERNAME,
                    message_id=message_id,
                    text=f"{base_text}\n\n⏳ Time left: {h:02d}:{m:02d}:{s:02d}"
                )
            except TelegramError:
                pass  # Message could be deleted or edit failed

            # Sleep 1 second for accurate countdown
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        return  # Graceful exit if bot is stopped
    except Exception as e:
        # Catch-all to prevent crash
        print(f"Unexpected error in countdown: {e}")

    # Final messages after countdown ends
    try:
        await context.bot.edit_message_text(
            chat_id=CHANNEL_USERNAME,
            message_id=message_id,
            text="⛔ Discount expired"
        )
    except TelegramError:
        pass

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"🚫 {base_text} has officially expired."
        )
    except TelegramError:
        pass

async def safe_reply(update: Update, text: str):
    """Send a reply safely without crashing."""
    try:
        await update.message.reply_text(text)
    except Exception:
        pass

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("countdown", countdown))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
