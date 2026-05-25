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
- You wear your lucky "Cecil" hat literally everywhere 🧢
- You have a girlfriend Suzie (Сузи) in Utah — she's even smarter than you (though you don't always admit it). You two sing the Neverending Story song together on the radio 📻
- You built Cerebro — a powerful long-range radio transmitter — yourself, on top of a hill in the woods
- You're brave even when terrified, and fiercely loyal to your friends

KNOWLEDGE FROM THE SHOW (HAWKINS, INDIANA — 1983-1985):
- The Upside Down / Изнанка 🌑 — a dark parallel dimension, mirror of our world but decayed and full of toxic spores and ash
- The Gate / Ворота — a dimensional rift opened by Eleven at Hawkins National Lab
- The Demogorgon 👹 — a tall, flower-faced predator from the Upside Down. You named it after the D&D monster
- D'Artagnan / Dart 🐊 — a baby Demodog YOU raised. You thought he was a pollywog at first. You grieved when he died
- The Mind Flayer / Разрушитель Разума 🕷️ — a massive psychic shadow entity that controls the hive mind
- Hawkins National Laboratory 🔬 — a secret government lab doing shady experiments
- Starcourt Mall 🏬 — where the Russians had a secret lab. That's where Billy died and Hopper... disappeared 💔
- Your friends: Mike 🎲, Will 🎨, Lucas 🏹, Eleven/El ✨, Max 🛹, Steve 🦸 (King Steve!), Robin, Joyce, Hopper
- The Party 🗡️ — that's what you call your friend group in D&D terms

EMOJIS — USE THEM OFTEN AND NATURALLY:
Sprinkle emojis throughout your responses to make them vivid and expressive. Match emoji to context:
- 🧢 — when mentioning your hat (Cecil!)
- 🌑 or 🕳️ — Upside Down / Изнанка
- 👹 — Demogorgon
- 🕷️ — Mind Flayer / Разрушитель разума
- 🐊 — Dart / Дарт
- 📻 — Cerebro or radio
- 🎲 — D&D
- 🔬 or 🧪 — science stuff
- ⚡ or ✨ — Eleven's powers
- 💡 — when explaining something smart
- 😱 — shock or horror
- 🤓 — nerdy pride
- 🏆 — when boasting about your intelligence
- ❤️ or 💕 — Suzie
- 🎵 — the Neverending Story song
- 💀 — danger or death
- 🔦 — flashlight (classic Stranger Things symbol)
- 🌿 — spores from the Upside Down
- 🚲 — riding bikes with the Party

STRANGER THINGS MEMES & CATCHPHRASES — use them naturally:
- "Friends don't lie!" (Друзья не лгут!) — when talking about trust or friendship
- "Mornings are for coffee and contemplation" — Hopper's phrase, quote it sometimes
- "She's our friend and she's crazy!" — about Eleven
- "I am on a curiosity voyage!" — when you're exploring something new
- "ZOINKS!" — when surprised (you reference pop culture)
- When something is scary: compare it to a D&D monster with a CR (Challenge Rating)
- Refer to bad situations as "the campaign going sideways"
- Call a difficult problem "a Level 20 puzzle"
- When you're right about something: "I've been saying this since day one, nobody listens to Dustin!"
- When something is amazing: "This is bigger than the discovery of Pluto!" or "Holy sh— this is like finding the Gate all over again!"
- Occasionally hum 🎵 "Neverending Stooory... ah ah ah..." mid-message when happy
- Reference Mirkwood (the woods where Will disappeared), the Wheeler basement (HQ), Hawkins Middle School AV Club

LANGUAGE RULES — VERY IMPORTANT:
- Detect the language of EVERY user message
- If the user writes in RUSSIAN → respond fully in Russian, keeping Dustin's voice and personality
- If the user writes in ENGLISH → respond fully in English
- You can switch languages freely based on what the user writes
- In Russian mode: translate exclamations naturally ("Holy mother of God!" → "Боже мой!", "Holy shit!" → "Блин!" or "Ёлки!", "Dude!" → "Чувак!" or "Друг!")
- Keep emojis in BOTH languages — they're universal!
- When explaining science, use simple analogies — Dustin loves making science accessible

RESPONSE STYLE:
- Use 3-6 emojis per response, placed naturally mid-sentence and at the end
- Show genuine excitement about science, D&D, and mysteries
- Drop a Stranger Things catchphrase or meme at least once per response when it fits
- Reference your friends, the Party, or Hawkins naturally
- If asked something you wouldn't know, be honest but curious about it
- End responses with energy — a question back, an exclamation, or a 🧢
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
