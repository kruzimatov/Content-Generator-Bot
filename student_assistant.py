import os
import tempfile
import fitz  # PyMuPDF
from docx import Document
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from utils import ai_request, send_long_message

# Conversation states
STU_UPLOAD, STU_ACTION, STU_QUESTION, STU_TRANSLATE_LANG = range(40, 44)

# Store user data per chat
user_data = {}

# Max characters to send to AI (GPT context limit safety)
MAX_TEXT_LENGTH = 12000


def extract_pdf_text(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_docx_text(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def truncate_text(text: str) -> str:
    if len(text) > MAX_TEXT_LENGTH:
        return text[:MAX_TEXT_LENGTH] + "\n\n[... matn qisqartirildi ...]"
    return text


# --- Handlers ---

async def stu_upload(update: Update, context) -> int:
    chat_id = update.message.chat_id
    doc = update.message.document

    if not doc:
        await update.message.reply_text(
            "⚠️ Iltimos, PDF yoki DOCX fayl yuboring."
        )
        return STU_UPLOAD

    file_name = doc.file_name or ""
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""

    if ext not in ("pdf", "docx", "doc"):
        await update.message.reply_text(
            "⚠️ Faqat PDF yoki DOCX fayl qabul qilinadi.\n"
            "Qaytadan yuboring."
        )
        return STU_UPLOAD

    await update.message.reply_text("⏳ Fayl yuklanmoqda va o'qilmoqda...")

    # Download file
    file = await doc.get_file()
    tmp_path = os.path.join(tempfile.gettempdir(), f"stu_{chat_id}.{ext}")
    await file.download_to_drive(tmp_path)

    # Extract text
    try:
        if ext == "pdf":
            text = extract_pdf_text(tmp_path)
        else:
            text = extract_docx_text(tmp_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Faylni o'qishda xatolik: {e}")
        return STU_UPLOAD
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not text or len(text) < 50:
        await update.message.reply_text(
            "⚠️ Faylda matn topilmadi yoki juda qisqa.\n"
            "Boshqa fayl yuboring."
        )
        return STU_UPLOAD

    user_data[chat_id] = {
        "text": text,
        "file_name": file_name,
    }

    page_count = len(text) // 2000 + 1
    keyboard = [
        [
            InlineKeyboardButton("📚 Qisqacha xulosa", callback_data="stu_summary"),
            InlineKeyboardButton("📊 Asosiy fikrlar", callback_data="stu_keypoints"),
        ],
        [
            InlineKeyboardButton("📝 Konspekt", callback_data="stu_notes"),
            InlineKeyboardButton("❓ Test savollar", callback_data="stu_quiz"),
        ],
        [
            InlineKeyboardButton("🔍 Savol berish", callback_data="stu_ask"),
            InlineKeyboardButton("🌐 Tarjima", callback_data="stu_translate"),
        ],
        [
            InlineKeyboardButton("📄 Referat yordam", callback_data="stu_essay"),
        ],
    ]

    await update.message.reply_text(
        f"✅ Fayl qabul qilindi: {file_name}\n"
        f"📄 Taxminan {page_count} sahifa matn\n\n"
        "Nima qilmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return STU_ACTION


async def stu_action(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if chat_id not in user_data:
        await query.edit_message_text(
            "⚠️ Fayl topilmadi. /start bosib qaytadan boshlang."
        )
        return ConversationHandler.END

    text = truncate_text(user_data[chat_id]["text"])
    action = query.data

    if action == "stu_ask":
        await query.edit_message_text(
            "🔍 Hujjat bo'yicha savolingizni yozing:"
        )
        return STU_QUESTION

    if action == "stu_translate":
        keyboard = [
            [
                InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="stu_tr_uz"),
                InlineKeyboardButton("🇬🇧 English", callback_data="stu_tr_en"),
            ],
            [
                InlineKeyboardButton("🇷🇺 Ruscha", callback_data="stu_tr_ru"),
            ],
        ]
        await query.edit_message_text(
            "🌐 Qaysi tilga tarjima qilish kerak?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return STU_TRANSLATE_LANG

    await query.edit_message_text("⏳ AI ishlamoqda...")

    prompts = {
        "stu_summary": (
            "You are a study assistant. Summarize the following document in 1-2 pages. "
            "Make it clear and easy to understand for a student.\n\n"
            "FORMATTING: No markdown (**, ##, ```). Plain text and emoji only. "
            "Use section headers ending with colon. Write in O'zbek language.\n\n"
            f"DOCUMENT:\n{text}"
        ),
        "stu_keypoints": (
            "You are a study assistant. Extract the KEY POINTS from this document. "
            "List 5-10 most important ideas, each with a brief explanation.\n\n"
            "FORMATTING: No markdown. Use numbered list with emoji. Write in O'zbek language.\n\n"
            f"DOCUMENT:\n{text}"
        ),
        "stu_notes": (
            "You are a study assistant. Create a structured LECTURE NOTES / KONSPEKT from this document. "
            "Organize by topics, include definitions, key terms, and important details. "
            "Make it suitable for exam preparation.\n\n"
            "FORMATTING: No markdown. Plain text, emoji headers ending with colon. Write in O'zbek language.\n\n"
            f"DOCUMENT:\n{text}"
        ),
        "stu_quiz": (
            "You are a study assistant. Create 10 TEST QUESTIONS based on this document.\n\n"
            "Include:\n"
            "- 5 multiple choice questions (A, B, C, D) with correct answer marked\n"
            "- 3 true/false questions with answers\n"
            "- 2 open-ended questions with brief model answers\n\n"
            "FORMATTING: No markdown. Plain text, numbered. Write in O'zbek language.\n\n"
            f"DOCUMENT:\n{text}"
        ),
        "stu_essay": (
            "You are a study assistant helping a student write an essay/referat. "
            "Based on this document, create:\n\n"
            "1. ESSAY PLAN (kirish, asosiy qism, xulosa)\n"
            "2. THESIS STATEMENT (asosiy g'oya - 1 jumla)\n"
            "3. INTRODUCTION draft (kirish qismi - 1 paragraf)\n"
            "4. KEY ARGUMENTS (3-4 ta dalil ro'yxati)\n"
            "5. CONCLUSION draft (xulosa - 1 paragraf)\n\n"
            "FORMATTING: No markdown. Plain text, emoji headers ending with colon. Write in O'zbek language.\n\n"
            f"DOCUMENT:\n{text}"
        ),
    }

    prompt = prompts.get(action, prompts["stu_summary"])

    try:
        result = ai_request(
            "You are a helpful study assistant for university students. Write in O'zbek language.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik: {e}"

    await send_long_message(query.message, result)
    await _send_again_menu(query.message)
    return STU_ACTION


async def stu_question(update: Update, context) -> int:
    chat_id = update.message.chat_id
    question = update.message.text.strip()

    if chat_id not in user_data:
        await update.message.reply_text(
            "⚠️ Fayl topilmadi. /start bosib qaytadan boshlang."
        )
        return ConversationHandler.END

    text = truncate_text(user_data[chat_id]["text"])
    await update.message.reply_text("⏳ Javob izlanmoqda...")

    prompt = (
        f"You are a study assistant. Answer the student's question based ONLY on this document.\n"
        f"If the answer is not in the document, say so.\n\n"
        f"DOCUMENT:\n{text}\n\n"
        f"STUDENT QUESTION: {question}\n\n"
        f"FORMATTING: No markdown. Plain text. Write in O'zbek language."
    )

    try:
        result = ai_request(
            "You are a helpful study assistant. Answer based on the document. Write in O'zbek language.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik: {e}"

    await send_long_message(update.message, result)
    await _send_again_menu(update.message)
    return STU_ACTION


async def stu_translate(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if chat_id not in user_data:
        await query.edit_message_text(
            "⚠️ Fayl topilmadi. /start bosib qaytadan boshlang."
        )
        return ConversationHandler.END

    lang_map = {
        "stu_tr_uz": "O'zbek",
        "stu_tr_en": "English",
        "stu_tr_ru": "Russian",
    }
    lang = lang_map.get(query.data, "O'zbek")
    text = truncate_text(user_data[chat_id]["text"])

    await query.edit_message_text(f"⏳ {lang} tiliga tarjima qilinmoqda...")

    prompt = (
        f"Translate the following document text into {lang} language. "
        f"Keep the structure and meaning. Make it natural and readable.\n\n"
        f"FORMATTING: No markdown (**, ##, ```). Plain text only.\n\n"
        f"TEXT:\n{text}"
    )

    try:
        result = ai_request(
            f"You are a professional translator. Translate accurately into {lang}.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik: {e}"

    await send_long_message(query.message, result)
    await _send_again_menu(query.message)
    return STU_ACTION


async def _send_again_menu(message):
    keyboard = [
        [
            InlineKeyboardButton("📚 Xulosa", callback_data="stu_summary"),
            InlineKeyboardButton("📊 Asosiy fikrlar", callback_data="stu_keypoints"),
        ],
        [
            InlineKeyboardButton("📝 Konspekt", callback_data="stu_notes"),
            InlineKeyboardButton("❓ Test", callback_data="stu_quiz"),
        ],
        [
            InlineKeyboardButton("🔍 Savol", callback_data="stu_ask"),
            InlineKeyboardButton("🌐 Tarjima", callback_data="stu_translate"),
        ],
        [
            InlineKeyboardButton("📄 Referat", callback_data="stu_essay"),
            InlineKeyboardButton("🏠 Bosh menyu", callback_data="stu_done"),
        ],
    ]
    await message.reply_text(
        "Yana nima qilmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def stu_done(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_data.pop(chat_id, None)
    await query.edit_message_text("✅ Yakunlandi! /start bosib qaytadan boshlang.")
    return ConversationHandler.END
