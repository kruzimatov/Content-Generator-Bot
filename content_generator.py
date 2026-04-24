from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from utils import ai_request, send_long_message

# Conversation states
NICHE, TONE, PLATFORM = range(3)

# Store user selections per chat
user_data = {}


def build_content_prompt(niche: str, tone: str, platform: str) -> str:
    return (
        f"Sen professional SMM mutaxassisan va kontent yozuvchisan.\n\n"
        f"Menga \"{niche}\" bo'yicha {platform} uchun PROFESSIONAL kontent yarat.\n"
        f"Ton: {tone}\n\n"
        f"Quyidagilarni ber:\n\n"
        f"1. POST G'OYA — nima haqida yozish kerakligi, 2-3 jumla bilan tushuntir\n\n"
        f"2. TAYYOR POST — bu eng muhim qism! Post kamida 150-250 so'z bo'lsin. "
        f"Post qiziqarli, sotuvchi, jalb qiluvchi bo'lsin. "
        f"Muammo-yechim formatida yoz. Avval auditoriyaning muammosini ko'rsat, "
        f"keyin yechim taklif qil. Oxirida kuchli CTA (harakatga chaqirish) bo'lsin. "
        f"Paragraflar orasida bo'sh qator qo'y. Emoji bilan bezat.\n\n"
        f"3. CAPTION — {platform} uchun mos, 2-3 jumla, emotsional va qiziqarli\n\n"
        f"4. HASHTAGLAR — 10 ta relevant hashtag\n\n"
        f"FORMATLASH QOIDALARI:\n"
        f"- Markdown belgilar ISHLATMA: **, ##, ###, ---, ``` MUMKIN EMAS\n"
        f"- Faqat oddiy tekst va emoji ishlat\n"
        f"- Bo'limlarni quyidagicha ajrat:\n\n"
        f"🧠 POST G'OYA:\n"
        f"(g'oya matni)\n\n"
        f"📝 TAYYOR POST:\n"
        f"(to'liq uzun post matni)\n\n"
        f"✍️ CAPTION:\n"
        f"(caption matni)\n\n"
        f"🏷 HASHTAGLAR:\n"
        f"#hashtag1 #hashtag2 ...\n\n"
        f"Kontent {platform} ga copy-paste qilsa bo'ladigan darajada tayyor bo'lsin."
    )


async def content_niche(update: Update, context) -> int:
    chat_id = update.message.chat_id
    user_data[chat_id] = {"niche": update.message.text.strip()}

    keyboard = [
        [
            InlineKeyboardButton("📢 Sotuvchi", callback_data="sotuvchi"),
            InlineKeyboardButton("🎩 Rasmiy", callback_data="rasmiy"),
        ],
        [
            InlineKeyboardButton("😎 Norasmiy", callback_data="norasmiy"),
            InlineKeyboardButton("🔥 Motivatsion", callback_data="motivatsion"),
        ],
    ]
    await update.message.reply_text(
        "✅ Niche qabul qilindi!\n\n🎨 Tonni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return TONE


async def content_tone(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data[chat_id]["tone"] = query.data

    keyboard = [
        [
            InlineKeyboardButton("📸 Instagram", callback_data="Instagram"),
            InlineKeyboardButton("✈️ Telegram", callback_data="Telegram"),
        ],
    ]
    await query.edit_message_text(
        f"🎨 Ton: {query.data}\n\n📱 Platformni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return PLATFORM


async def content_platform(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data[chat_id]["platform"] = query.data

    data = user_data[chat_id]
    await query.edit_message_text("⏳ Kontent generatsiya qilinmoqda...")

    prompt = build_content_prompt(data["niche"], data["tone"], data["platform"])

    try:
        result = ai_request(
            "Sen professional SMM mutaxassisan. Faqat o'zbek tilida javob ber.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik yuz berdi: {e}"

    await send_long_message(query.message, result)
    await query.message.reply_text("🔄 Qaytadan boshlash uchun /start bosing!")
    user_data.pop(chat_id, None)
    return ConversationHandler.END
