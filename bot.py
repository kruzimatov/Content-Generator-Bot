import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)


from content_generator import (
    NICHE, TONE, PLATFORM,
    content_niche, content_tone, content_platform,
)
from client_finder import (
    DM_NICHE, DM_SERVICE, DM_PROFILE,
    dm_niche, dm_service, dm_profile,
)
from resume_generator import (
    CV_NAME, CV_JOB, CV_EXPERIENCE, CV_SKILLS, CV_PHOTO, CV_TEMPLATE, CV_LANGUAGE,
    cv_name, cv_job, cv_experience, cv_skills,
    cv_photo_choice, cv_photo_receive,
    cv_template, cv_language,
)
from med_reminder import (
    MED_NAME, MED_FREQUENCY, MED_TIME, MED_DURATION,
    med_action, med_delete, med_name_input,
    med_frequency, med_time_input, med_duration,
    restore_all_reminders,
)
from student_assistant import (
    STU_UPLOAD, STU_ACTION, STU_QUESTION, STU_TRANSLATE_LANG,
    stu_upload, stu_action, stu_question, stu_translate, stu_done,
)
from taxi_driver import (
    TAXI_MENU, TAXI_TRIP, TAXI_FUEL,
    taxi_action, taxi_trip_input, taxi_fuel_input,
)

load_dotenv()

MENU_STATE = 99

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📝 Kontent"), KeyboardButton("🔍 Mijoz DM")],
        [KeyboardButton("📄 Resume"), KeyboardButton("💊 Dori Eslatma")],
        [KeyboardButton("📚 Talaba"), KeyboardButton("🚕 Taxi")],
    ],
    resize_keyboard=True,
)


async def start(update: Update, context) -> int:
    await update.message.reply_text(
        "👋 Salom! Men AI Botman.\n\n"
        "Pastdagi tugmalardan birini tanlang:\n\n"
        "📝 Kontent — tayyor post, caption, hashtag\n"
        "🔍 Mijoz DM — target mijoz + personal DM\n"
        "📄 Resume — professional CV yaratish\n"
        "💊 Dori Eslatma — dori vaqti va tekshirish\n"
        "📚 Talaba — PDF/DOCX xulosa, test, tarjima\n"
        "🚕 Taxi — daromad, xarajat, foyda hisobi",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU_STATE


async def menu_text(update: Update, context) -> int:
    text = update.message.text

    if text == "📝 Kontent":
        await update.message.reply_text(
            "📝 KONTENT GENERATOR\n\n"
            "📌 Niche yozing:\n"
            "Masalan: AI kurs, Fitness, Biznes, Ta'lim, Restoran..."
        )
        return NICHE
    elif text == "🔍 Mijoz DM":
        await update.message.reply_text(
            "🔍 MIJOZ TOPISH + AUTO DM\n\n"
            "📌 Qaysi soha (niche) bo'yicha mijoz qidiryapsiz?\n"
            "Masalan: restoranlar, fitness trenerlar, onlayn do'konlar..."
        )
        return DM_NICHE
    elif text == "📄 Resume":
        await update.message.reply_text(
            "📄 RESUME GENERATOR\n\n"
            "Professional CV yaratamiz!\n\n"
            "📌 Ismingizni kiriting:"
        )
        return CV_NAME
    elif text == "💊 Dori Eslatma":
        from med_reminder import med_menu
        await med_menu(update.message)
        return MED_NAME
    elif text == "📚 Talaba":
        await update.message.reply_text(
            "📚 TALABA YORDAMCHI\n\n"
            "📄 PDF yoki DOCX fayl yuboring:\n"
            "(kitob, konspekt, maqola, referat...)"
        )
        return STU_UPLOAD
    elif text == "🚕 Taxi":
        from taxi_driver import taxi_menu
        await taxi_menu(update.message)
        return TAXI_MENU

    await update.message.reply_text("Pastdagi tugmalardan birini tanlang:", reply_markup=MAIN_KEYBOARD)
    return MENU_STATE


async def help_cmd(update: Update, context) -> None:
    await update.message.reply_text(
        "📖 YORDAM\n\n"
        "Mavjud buyruqlar:\n"
        "/start — Botni ishga tushirish\n"
        "/help — Yordam ko'rsatish\n"
        "/menu — Asosiy menyuga qaytish\n"
        "/cancel — Joriy amalni bekor qilish\n"
        "/about — Bot haqida ma'lumot\n\n"
        "Funksiyalar:\n"
        "📝 Kontent — Instagram, Telegram uchun post yaratish\n"
        "🔍 Mijoz DM — target auditoriya + shaxsiy DM yozish\n"
        "📄 Resume — professional CV (DOCX) yaratish\n"
        "💊 Dori Eslatma — dori vaqtini eslatish, ta'sir tekshirish\n"
        "📚 Talaba — PDF/DOCX fayl tahlili, xulosa, test\n"
        "🚕 Taxi — yo'lov, yoqilg'i hisobi va foyda tahlili",
        reply_markup=MAIN_KEYBOARD,
    )


async def about_cmd(update: Update, context) -> None:
    await update.message.reply_text(
        "🤖 AI Bot v1.0\n\n"
        "6 ta AI yordamchi bir botda:\n"
        "Kontent, Mijoz DM, Resume, Dori Eslatma,\n"
        "Talaba Yordamchi, Taxi Yordamchi\n\n"
        "AI: OpenAI GPT-4o-mini\n"
        "Framework: python-telegram-bot",
        reply_markup=MAIN_KEYBOARD,
    )


async def menu_cmd(update: Update, context) -> int:
    await update.message.reply_text(
        "📋 Asosiy menyu — pastdagi tugmalardan tanlang:",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU_STATE


async def cancel(update: Update, context) -> int:
    await update.message.reply_text(
        "❌ Bekor qilindi. Pastdagi tugmalardan tanlang:",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU_STATE


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("menu", "Asosiy menyu"),
        BotCommand("help", "Yordam"),
        BotCommand("cancel", "Bekor qilish"),
        BotCommand("about", "Bot haqida"),
    ])


def main():
    app = (
        Application.builder()
        .token(os.getenv("BOT_TOKEN"))
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .post_init(post_init)
        .build()
    )

    menu_filter = filters.Regex(
        r"^(📝 Kontent|🔍 Mijoz DM|📄 Resume|💊 Dori Eslatma|📚 Talaba|🚕 Taxi)$"
    )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(menu_filter, menu_text),
        ],
        states={
            MENU_STATE: [MessageHandler(menu_filter, menu_text)],
            # Content Generator
            NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, content_niche)],
            TONE: [CallbackQueryHandler(content_tone)],
            PLATFORM: [CallbackQueryHandler(content_platform)],
            # Client Finder
            DM_NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_niche)],
            DM_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_service)],
            DM_PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dm_profile)],
            # Resume Generator
            CV_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cv_name)],
            CV_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, cv_job)],
            CV_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cv_experience)],
            CV_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, cv_skills)],
            CV_PHOTO: [
                CallbackQueryHandler(cv_photo_choice, pattern="^cv_photo_"),
                MessageHandler(filters.PHOTO, cv_photo_receive),
            ],
            CV_TEMPLATE: [CallbackQueryHandler(cv_template, pattern="^cv_tpl_")],
            CV_LANGUAGE: [CallbackQueryHandler(cv_language, pattern="^cv_lang_")],
            # Med Reminder
            MED_NAME: [
                CallbackQueryHandler(med_action, pattern="^med_(add|list|check|remove)$"),
                CallbackQueryHandler(med_delete, pattern="^med_del_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, med_name_input),
            ],
            MED_FREQUENCY: [CallbackQueryHandler(med_frequency, pattern="^med_freq_")],
            MED_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_time_input)],
            MED_DURATION: [CallbackQueryHandler(med_duration, pattern="^med_dur_")],
            # Student Assistant
            STU_UPLOAD: [MessageHandler(filters.Document.ALL, stu_upload)],
            STU_ACTION: [
                CallbackQueryHandler(stu_action, pattern="^stu_(summary|keypoints|notes|quiz|ask|translate|essay)$"),
                CallbackQueryHandler(stu_done, pattern="^stu_done$"),
            ],
            STU_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, stu_question)],
            STU_TRANSLATE_LANG: [CallbackQueryHandler(stu_translate, pattern="^stu_tr_")],
            # Taxi Driver
            TAXI_MENU: [CallbackQueryHandler(taxi_action, pattern="^taxi_")],
            TAXI_TRIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_trip_input)],
            TAXI_FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, taxi_fuel_input)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            CommandHandler("menu", menu_cmd),
            MessageHandler(menu_filter, menu_text),
        ],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))

    # Restore saved medication reminders
    restore_all_reminders(app)

    print("🤖 Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
