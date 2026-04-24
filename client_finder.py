from telegram import Update
from telegram.ext import ConversationHandler

from utils import ai_request, send_long_message

# Conversation states
DM_NICHE, DM_SERVICE, DM_PROFILE = range(10, 13)

# Store user selections per chat
user_data = {}


async def dm_niche(update: Update, context) -> int:
    chat_id = update.message.chat_id
    user_data[chat_id] = {"dm_niche": update.message.text.strip()}

    await update.message.reply_text(
        "✅ Niche qabul qilindi!\n\n"
        "💼 Endi siz taklif qiladigan xizmatni yozing:\n"
        "Masalan: SMM xizmati, logo dizayn, web sayt yaratish, AI bot yaratish..."
    )
    return DM_SERVICE


async def dm_service(update: Update, context) -> int:
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
