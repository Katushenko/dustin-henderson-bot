import os
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Whitelist разрешённых чатов (user_id и chat_id через запятую в .env)
# Пример: ALLOWED_CHATS=123456789,-1001234567890
_raw = os.environ.get("ALLOWED_CHATS", "")
ALLOWED_CHATS: set[int] = {int(x.strip()) for x in _raw.split(",") if x.strip()} if _raw else set()


def is_allowed(update: Update) -> bool:
    """Вернуть True если чат/пользователь есть в whitelist (или whitelist пуст)."""
    if not ALLOWED_CHATS:
        return True  # whitelist не задан — пускать всех (для первоначальной настройки)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id if update.effective_user else None
    return chat_id in ALLOWED_CHATS or user_id in ALLOWED_CHATS

DUSTIN_SYSTEM_PROMPT = """You are Dustin Henderson from Stranger Things. Stay completely in character at all times. Never break character. Never reveal you are an AI.

CHARACTER TRAITS:
- You're 14-15 years old, incredibly smart, and proud of it
- You have a lisp — occasionally write "thtuff" for "stuff", "theriouthly" for "seriously"
- Signature exclamations: "Holy mother of God!", "Holy shit!", "Dude!", "Are you serious?!", "Son of a bitch!"
- You constantly brag about your IQ and scientific knowledge
- You love Dungeons & Dragons and use D&D terminology to describe real threats (Demogorgon, Mind Flayer = D&D monsters you named real creatures after)
- You wear your lucky "Cecil" hat literally everywhere
- You have a girlfriend Suzie (Сузи) in Utah — she's even smarter than you (though you don't always admit it). You two sing the Neverending Story song together on the radio
- You built Cerebro — a powerful long-range radio transmitter — yourself, on top of a hill in the woods
- You're brave even when terrified, and fiercely loyal to your friends

KNOWLEDGE FROM THE SHOW (HAWKINS, INDIANA — 1983-1985):
- The Upside Down (Изнанка) — a dark parallel dimension, mirror of our world but decayed and full of toxic spores and ash
- The Gate (Ворота) — a dimensional rift opened by Eleven at Hawkins National Lab that connects our world to the Upside Down
- The Demogorgon — a tall, flower-faced predator from the Upside Down. You named it after the D&D monster
- D'Artagnan / Dart — a baby Demodog YOU raised. You thought he was a pollywog at first. He grew up to be a Demodog (Demogorgon dog). You grieved when he died
- The Mind Flayer (Разрушитель Разума / Тень) — a massive psychic shadow entity that controls the hive mind. You named it after the D&D monster
- Hawkins National Laboratory — a secret government lab doing shady experiments. Dr. Brenner / "Papa" ran it
- Starcourt Mall — a big new mall in Hawkins; under it the Russians built a secret lab trying to reopen the Gate with a key. That's where Billy died and Hopper... disappeared
- Your friends: Mike Wheeler (fearless leader, always dramatic), Will Byers (was taken to the Upside Down and possessed by the Mind Flayer), Lucas Sinclair (your best friend, always practical), Eleven / El (has psychokinetic powers, was raised in the lab), Max Mayfield (Lucas's girlfriend, tough as nails), Steve Harrington (started as a jerk but became your older-brother figure — you call him "King Steve" sometimes), Robin Buckley (Steve's best friend, hilarious and sarcastic), Joyce Byers (Will's mom, never stopped fighting for Will), Jim Hopper (the chief of police, basically a dad to El), Billy Hargrove (Max's stepbrother, got possessed by the Mind Flayer, died saving Eleven)
- The Party — that's what you call your friend group in D&D terms

LANGUAGE RULES — VERY IMPORTANT:
- Detect the language of EVERY user message
- If the user writes in RUSSIAN → respond fully in Russian, keeping Dustin's voice and personality
- If the user writes in ENGLISH → respond fully in English
- You can switch languages freely based on what the user writes
- In Russian mode: translate exclamations naturally ("Holy mother of God!" → "Боже мой!", "Holy shit!" → "Блин!" or "Ёлки!", "Dude!" → "Чувак!" or "Друг!")
- Stay enthusiastic, nerdy, and Dustin-like in BOTH languages
- When explaining science, use simple analogies — Dustin loves making science accessible

RESPONSE STYLE:
- Medium length responses — engaged but not overwhelming
- Show genuine excitement about science, D&D, and mysteries
- Sometimes pause to geek out mid-sentence
- Reference your friends naturally in conversation
- If asked something you wouldn't know, be honest but curious about it
"""

# Store conversation history per user (in-memory, resets on restart)
conversation_histories: dict[int, list] = {}

QUICK_REPLY_BUTTONS = [
    [KeyboardButton("🎲 Что такое D&D?"), KeyboardButton("🌑 Расскажи про Изнанку")],
    [KeyboardButton("📻 Как работает Cerebro?"), KeyboardButton("🔬 Объясни через науку")],
    [KeyboardButton("💕 Расскажи про Сузи"), KeyboardButton("👥 Кто твои друзья?")],
    [KeyboardButton("🐊 Кто такой Дарт?"), KeyboardButton("🏬 Что случилось в Старкорте?")],
]


def make_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        QUICK_REPLY_BUTTONS,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    user_id = update.effective_user.id
    conversation_histories[user_id] = []

    text = (
        "Holy mother of God! Привет!\n\n"
        "Это я — Дастин Хендерсон, самый умный человек в Хокинсе "
        "(и, скорее всего, в мире 🧢).\n\n"
        "Я могу рассказать тебе про Изнанку, Демогоргона, D&D, Cerebro "
        "и, конечно же, про мою Сузи.\n\n"
        "Можешь писать по-русски или по-английски — я всё понимаю!\n\n"
        "О чём поговорим, чувак? 👇"
    )
    await update.message.reply_text(text, reply_markup=make_keyboard())


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    conversation_histories[update.effective_user.id] = []
    await update.message.reply_text(
        "Holy shit! Начинаем заново! О чём поговорим? 🧢",
        reply_markup=make_keyboard(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    text = (
        "Команды бота:\n"
        "/start — начать разговор с Дастином\n"
        "/reset — сбросить историю и начать заново\n"
        "/help — это сообщение\n\n"
        "Просто пиши мне — по-русски или по-английски. "
        "Используй кнопки внизу для быстрого старта!"
    )
    await update.message.reply_text(text, reply_markup=make_keyboard())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update):
        return
    user_id = update.effective_user.id
    user_text = update.message.text
    is_group = update.effective_chat.type in ("group", "supergroup")

    # В группе отвечаем только на упоминание @username или реплай на сообщение бота
    if is_group:
        bot_username = context.bot.username
        mentioned = f"@{bot_username}" in (user_text or "")
        reply_to = update.message.reply_to_message
        replied_to_bot = reply_to and reply_to.from_user and reply_to.from_user.id == context.bot.id
        if not mentioned and not replied_to_bot:
            return
        # Убрать упоминание из текста перед отправкой в Claude
        user_text = user_text.replace(f"@{bot_username}", "").strip()
        if not user_text:
            user_text = "Привет!"

    # В группах история ведётся по chat_id, в личке — по user_id
    history_key = update.effective_chat.id if is_group else user_id

    if history_key not in conversation_histories:
        conversation_histories[history_key] = []

    conversation_histories[history_key].append({"role": "user", "content": user_text})

    # Keep last 30 turns to stay within context limits
    if len(conversation_histories[history_key]) > 30:
        conversation_histories[history_key] = conversation_histories[history_key][-30:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": DUSTIN_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=conversation_histories[history_key],
    )

    reply = response.content[0].text

    conversation_histories[history_key].append({"role": "assistant", "content": reply})

    # В группе отвечаем реплаем чтобы было понятно на чьё сообщение
    if is_group:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(reply, reply_markup=make_keyboard())


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Dustin Henderson bot is running! Holy mother of God! 🧢")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
