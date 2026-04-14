import os
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Conversation states for Content Generator
NICHE, TONE, PLATFORM = range(3)

# Conversation states for Client Finder
DM_NICHE, DM_SERVICE, DM_PROFILE = range(10, 13)

# Store user selections per chat
user_data = {}


def clean_markdown(text: str) -> str:
    """Remove markdown symbols from AI response."""
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("```", "")
    text = text.replace("---", "")
    # Remove ## headers but keep the text
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.lstrip("# ")
        if line.startswith("#"):
            cleaned.append(stripped)
        else:
            cleaned.append(line)
    return "\n".join(cleaned)


def ai_request(system_msg: str, user_msg: str) -> str:
    """Send a request to OpenAI and return the response text."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=3000,
    )
    return clean_markdown(response.choices[0].message.content)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📝 CONTENT GENERATOR (Day 1 + Day 2)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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


async def start(update: Update, context) -> None:
    """Main menu with two options."""
    keyboard = [
        [InlineKeyboardButton("📝 Kontent Generator", callback_data="menu_content")],
        [InlineKeyboardButton("🔍 Mijoz Topish + DM", callback_data="menu_dm")],
    ]
    await update.message.reply_text(
        "👋 Salom! Men AI SMM Botman.\n\n"
        "Nima qilmoqchisiz?\n\n"
        "📝 Kontent Generator — tayyor post, caption, hashtag yaratish\n"
        "🔍 Mijoz Topish + DM — target mijoz analizi va personal DM yozish",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def menu_choice(update: Update, context) -> None:
    """Route from main menu to the chosen feature."""
    query = update.callback_query
    await query.answer()

    if query.data == "menu_content":
        await query.edit_message_text(
            "📝 KONTENT GENERATOR\n\n"
            "📌 Niche yozing:\n"
            "Masalan: AI kurs, Fitness, Biznes, Ta'lim, Restoran..."
        )
        return NICHE
    elif query.data == "menu_dm":
        await query.edit_message_text(
            "🔍 MIJOZ TOPISH + AUTO DM\n\n"
            "📌 Qaysi soha (niche) bo'yicha mijoz qidiryapsiz?\n"
            "Masalan: restoranlar, fitness trenerlar, onlayn do'konlar..."
        )
        return DM_NICHE


# --- Content Generator Flow ---

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 CLIENT FINDER + AUTO DM (Day 3)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def dm_niche(update: Update, context) -> int:
    """Receive target niche for client finding."""
    chat_id = update.message.chat_id
    user_data[chat_id] = {"dm_niche": update.message.text.strip()}

    await update.message.reply_text(
        "✅ Niche qabul qilindi!\n\n"
        "💼 Endi siz taklif qiladigan xizmatni yozing:\n"
        "Masalan: SMM xizmati, logo dizayn, web sayt yaratish, AI bot yaratish..."
    )
    return DM_SERVICE


async def dm_service(update: Update, context) -> int:
    """Receive service description and ask for client profile."""
    chat_id = update.message.chat_id
    user_data[chat_id]["service"] = update.message.text.strip()

    await update.message.reply_text(
        "✅ Xizmat qabul qilindi!\n\n"
        "👤 Endi mijoz profilini yozing:\n"
        "Quyidagilarni kiriting:\n\n"
        "1. Mijoz ismi yoki kompaniya nomi\n"
        "2. Bio (profil haqida qisqa ma'lumot)\n"
        "3. Nima bilan shug'ullanadi\n"
        "4. Qanday postlar qiladi\n\n"
        "Barchasini bir xabarda yozing."
    )
    return DM_PROFILE


async def dm_profile(update: Update, context) -> int:
    """Analyze client profile and generate personalized DM."""
    chat_id = update.message.chat_id
    profile_info = update.message.text.strip()
    data = user_data[chat_id]

    await update.message.reply_text("⏳ Mijoz tahlil qilinmoqda va DM yozilmoqda...")

    prompt = (
        f"Sen cold outreach bo'yicha ekspertsan. Instagram DM orqali mijoz topishda mutaxassisan.\n\n"
        f"Mening xizmatim: {data['service']}\n"
        f"Target niche: {data['dm_niche']}\n\n"
        f"Mijoz profili:\n{profile_info}\n\n"
        f"Quyidagilarni qil:\n\n"
        f"📊 MIJOZ TAHLILI:\n"
        f"- Faoliyati (1 jumla)\n"
        f"- Aniq muammosi (raqamlar bilan, masalan: 3000 follower lekin 20 like = 0.6% engagement)\n"
        f"- Mening xizmatim nima natija beradi (aniq raqam yoki natija)\n\n"
        f"💬 3 TA DM VARIANTI:\n\n"
        f"MUHIM: Har bir DM FAQAT 2 jumla bo'lsin! Birinchi jumla - kirish, ikkinchi jumla - savol. Uzun yozma!\n\n"
        f"DM 1 (MUAMMO): Muammoni ayt + yordam taklif qil\n"
        f"DM 2 (MAQTOV): Ishini maqta + taklif\n"
        f"DM 3 (NATIJA): O'z natijangni ko'rsat + taklif\n\n"
        f"Namuna (aynan shu uzunlikda yoz):\n"
        f"'Sardor aka, Oasis Cafe sahifasini ko'rdim — taomlar zo'r lekin sahifa potentsialining 10% ini ishlatyapti. Sizga bepul tahlil qilib beraymi?'\n\n"
        f"🔄 FOLLOW-UP (2 kun keyin):\n"
        f"- Faqat 1 jumla\n"
        f"- Yangi qiymat qo'sh (bepul narsa taklif qil)\n"
        f"- Namuna: 'Sardor aka, sizning sahifangiz uchun 3 ta kontent g'oya tayyorladim — yuboraymi?'\n\n"
        f"FORMATLASH: Markdown belgilar ishlatma. Faqat oddiy tekst va emoji. Grammatik xato qilma."
    )

    try:
        result = ai_request(
            "Sen professional biznes konsultant va sotuvchisan. Mijozlarni tahlil qilish va ularga personal xabar yozishda mutaxassisan. Faqat o'zbek tilida javob ber.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik yuz berdi: {e}"

    await send_long_message(update.message, result)
    await update.message.reply_text("🔄 Qaytadan boshlash uchun /start bosing!")
    user_data.pop(chat_id, None)
    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def send_long_message(message, text: str) -> None:
    """Split and send messages that exceed Telegram's 4096 char limit."""
    if len(text) > 4000:
        parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await message.reply_text(part)
    else:
        await message.reply_text(text)


async def cancel(update: Update, context) -> int:
    await update.message.reply_text("❌ Bekor qilindi. /start bosib qaytadan boshlang.")
    return ConversationHandler.END


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Content Generator conversation
    content_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_choice, pattern="^menu_")],
        states={
            NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, content_niche)],
            TONE: [CallbackQueryHandler(content_tone)],
            PLATFORM: [CallbackQueryHandler(content_platform)],
            DM_NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_niche)],
            DM_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_service)],
            DM_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_profile)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(content_conv)

    print("🤖 Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
