import os
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


async def start(update: Update, context) -> None:
    keyboard = [
        [InlineKeyboardButton("📝 Kontent Generator", callback_data="menu_content")],
        [InlineKeyboardButton("🔍 Mijoz Topish + DM", callback_data="menu_dm")],
        [InlineKeyboardButton("📄 Resume Generator", callback_data="menu_resume")],
        [InlineKeyboardButton("💊 Dori Eslatma", callback_data="menu_med")],
        [InlineKeyboardButton("📚 Talaba Yordamchi", callback_data="menu_student")],
        [InlineKeyboardButton("🚕 Taxi Yordamchi", callback_data="menu_taxi")],
    ]
    await update.message.reply_text(
        "👋 Salom! Men AI Botman.\n\n"
        "Nima qilmoqchisiz?\n\n"
        "📝 Kontent Generator — tayyor post, caption, hashtag yaratish\n"
        "🔍 Mijoz Topish + DM — target mijoz analizi va personal DM yozish\n"
        "📄 Resume Generator — professional CV va cover letter yaratish\n"
        "💊 Dori Eslatma — dori eslatma, tekshirish va ma'lumot\n"
        "📚 Talaba Yordamchi — PDF/DOCX xulosa, konspekt, test, tarjima\n"
        "🚕 Taxi Yordamchi — daromad, xarajat, foyda hisobi",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def menu_choice(update: Update, context) -> None:
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
    elif query.data == "menu_resume":
        await query.edit_message_text(
            "📄 RESUME GENERATOR\n\n"
            "Professional CV yaratamiz!\n\n"
            "📌 Ismingizni kiriting:"
        )
        return CV_NAME
    elif query.data == "menu_med":
        from med_reminder import med_menu
        await med_menu(query.message, edit=True)
        return MED_NAME
    elif query.data == "menu_student":
        await query.edit_message_text(
            "📚 TALABA YORDAMCHI\n\n"
            "📄 PDF yoki DOCX fayl yuboring:\n"
            "(kitob, konspekt, maqola, referat...)"
        )
        return STU_UPLOAD
    elif query.data == "menu_taxi":
        from taxi_driver import taxi_menu
        await taxi_menu(query.message, edit=True)
        return TAXI_MENU


async def cancel(update: Update, context) -> int:
    await update.message.reply_text("❌ Bekor qilindi. /start bosib qaytadan boshlang.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_choice, pattern="^menu_")],
        states={
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
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    # Restore saved medication reminders
    restore_all_reminders(app)

    print("🤖 Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
