import asyncio
import os
from datetime import datetime, timedelta

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@certified_escrow")

_default_authorized = {8182255472}
_authorized_env = os.getenv("AUTHORIZED_USERS")
if _authorized_env:
    AUTHORIZED_USERS = {int(x.strip()) for x in _authorized_env.split(",") if x.strip()}
else:
    AUTHORIZED_USERS = _default_authorized


def format_time(seconds: int) -> str:
    """Format seconds into compact time like '2h 5m 10s', hiding zero values."""
    seconds = max(0, seconds)

    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)

    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0 or not parts:
        parts.append(f"{s}s")

    return " ".join(parts)


async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await safe_reply(update, "🚫 You are not authorized to use this bot.")
        return

    if update.effective_chat.type != "private":
        await safe_reply(update, "⚠️ Please use this command in a private chat with the bot.")
        return

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
        await safe_reply(update, "❌ Invalid time format. Use HH:MM.")
        return

    end_time = datetime.utcnow() + timedelta(hours=hours, minutes=minutes)
    total_seconds = hours * 3600 + minutes * 60

    # Initial message
    try:
        sent_message = await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=f"{base_text}\n\n⏳ Time left: {format_time(total_seconds)}"
        )
        message_id = sent_message.message_id
    except TelegramError as e:
        await safe_reply(update, f"❌ Failed to send message: {e}")
        return

    # Countdown loop (update every 5 seconds)
    try:
        while True:
            remaining = end_time - datetime.utcnow()
            seconds_left = int(remaining.total_seconds())

            if seconds_left < 0:
                break

            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_USERNAME,
                    message_id=message_id,
                    text=f"{base_text}\n\n⏳ Time left: {format_time(seconds_left)}"
                )
            except TelegramError:
                pass

            await asyncio.sleep(5)

    except asyncio.CancelledError:
        return
    except Exception as e:
        print(f"Countdown error: {e}")

    # Expiration announcement (separate message)
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text="🚫 The discount has officially expired."
        )
    except TelegramError:
        pass


async def safe_reply(update: Update, text: str):
    try:
        await update.message.reply_text(text)
    except Exception:
        pass


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("countdown", countdown))
    app.run_polling()


if __name__ == "__main__":
    main()
