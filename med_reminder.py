import os
import json
import tempfile
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

from utils import ai_request, send_long_message

# Conversation states
MED_NAME, MED_FREQUENCY, MED_TIME, MED_DURATION = range(30, 34)

# Persistent storage file
DATA_FILE = os.path.join(os.path.dirname(__file__), "med_data.json")

# Store user selections per chat
user_data = {}


def load_med_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_med_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_meds(chat_id: int) -> list:
    data = load_med_data()
    return data.get(str(chat_id), [])


def add_user_med(chat_id: int, med: dict):
    data = load_med_data()
    key = str(chat_id)
    if key not in data:
        data[key] = []
    data[key].append(med)
    save_med_data(data)


def remove_user_med(chat_id: int, index: int):
    data = load_med_data()
    key = str(chat_id)
    if key in data and 0 <= index < len(data[key]):
        data[key].pop(index)
        save_med_data(data)


# --- Reminder callback (runs on schedule) ---

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    med_name = job.data["med_name"]
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"💊 ESLATMA: {med_name} ichish vaqti keldi!\n\n"
             f"Dozangizni qabul qiling va sog'lom bo'ling! 💪",
    )


def schedule_med_reminders(app, chat_id: int, med: dict):
    """Schedule daily reminders for a medication."""
    job_queue = app.job_queue
    med_name = med["name"]

    for t in med["times"]:
        hour, minute = map(int, t.split(":"))
        job_name = f"med_{chat_id}_{med_name}_{t}"

        # Remove existing job with same name
        current_jobs = job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

        job_queue.run_daily(
            send_reminder,
            time=time(hour=hour, minute=minute),
            chat_id=chat_id,
            name=job_name,
            data={"med_name": med_name},
        )


def remove_med_jobs(app, chat_id: int, med_name: str):
    """Remove all scheduled jobs for a medication."""
    job_queue = app.job_queue
    jobs = job_queue.jobs()
    for job in jobs:
        if job.name and job.name.startswith(f"med_{chat_id}_{med_name}_"):
            job.schedule_removal()


# --- Handlers ---

async def med_menu(message, edit=False):
    """Show medication menu."""
    keyboard = [
        [InlineKeyboardButton("💊 Dori qo'shish", callback_data="med_add")],
        [InlineKeyboardButton("📋 Dorilarim ro'yxati", callback_data="med_list")],
        [InlineKeyboardButton("🔍 Dori tekshirish", callback_data="med_check")],
        [InlineKeyboardButton("🗑 Dorini o'chirish", callback_data="med_remove")],
    ]
    text = (
        "💊 DORI ESLATMA TIZIMI\n\n"
        "Nima qilmoqchisiz?\n\n"
        "💊 Dori qo'shish — yangi dori va eslatma\n"
        "📋 Dorilarim — barcha dorilar ro'yxati\n"
        "🔍 Tekshirish — dorilar o'zaro ta'siri\n"
        "🗑 O'chirish — dorini ro'yxatdan chiqarish"
    )
    if edit:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def med_action(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "med_add":
        await query.edit_message_text(
            "💊 YANGI DORI QO'SHISH\n\n"
            "📌 Dori nomini yozing:\n"
            "Masalan: Paracetamol, Ibuprofen, Vitamin D..."
        )
        return MED_NAME

    elif query.data == "med_list":
        meds = get_user_meds(chat_id)
        if not meds:
            await query.edit_message_text(
                "📋 Sizda hali dori qo'shilmagan.\n\n"
                "🔄 /start bosib qaytadan boshlang."
            )
        else:
            lines = ["📋 SIZNING DORILARINGIZ:\n"]
            for i, med in enumerate(meds, 1):
                times_str = ", ".join(med["times"])
                lines.append(
                    f"{i}. 💊 {med['name']}\n"
                    f"   Kuniga: {med['frequency']} marta\n"
                    f"   Vaqti: {times_str}\n"
                    f"   Muddat: {med['duration']} kun\n"
                )
            lines.append("\n🔄 /start bosib qaytadan boshlang.")
            await query.edit_message_text("\n".join(lines))
        return ConversationHandler.END

    elif query.data == "med_check":
        meds = get_user_meds(chat_id)
        if len(meds) < 2:
            await query.edit_message_text(
                "⚠️ Tekshirish uchun kamida 2 ta dori kerak.\n\n"
                "🔄 /start bosib qaytadan boshlang."
            )
            return ConversationHandler.END

        med_names = [m["name"] for m in meds]
        await query.edit_message_text("⏳ Dorilar tekshirilmoqda...")

        prompt = (
            f"Patient is taking these medications: {', '.join(med_names)}\n\n"
            f"Please analyze:\n"
            f"1. DRUG INTERACTIONS - Are there any dangerous interactions between these drugs?\n"
            f"2. SIDE EFFECTS - Common side effects for each drug\n"
            f"3. WARNINGS - Important warnings when taking these together\n"
            f"4. RECOMMENDATIONS - General advice\n\n"
            f"FORMATTING: No markdown symbols (**, ##, ```). Use plain text and emoji only.\n"
            f"Write section headers ending with colon like:\n"
            f"DRUG INTERACTIONS:\n"
            f"SIDE EFFECTS:\n"
            f"WARNINGS:\n"
            f"RECOMMENDATIONS:\n\n"
            f"Write in O'zbek language."
        )

        try:
            result = ai_request(
                "You are a pharmaceutical assistant. Provide drug interaction information. "
                "DISCLAIMER: Always remind that this is AI-generated info, not medical advice. "
                "Write in O'zbek language.",
                prompt,
            )
        except Exception as e:
            result = f"❌ Xatolik: {e}"

        await send_long_message(query.message, result)
        await query.message.reply_text("🔄 /start bosib qaytadan boshlang.")
        return ConversationHandler.END

    elif query.data == "med_remove":
        meds = get_user_meds(chat_id)
        if not meds:
            await query.edit_message_text(
                "📋 Sizda dori yo'q.\n\n🔄 /start bosib qaytadan boshlang."
            )
            return ConversationHandler.END

        keyboard = []
        for i, med in enumerate(meds):
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑 {med['name']}", callback_data=f"med_del_{i}"
                )
            ])
        await query.edit_message_text(
            "🗑 Qaysi dorini o'chirmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return MED_NAME  # reuse state for delete callback


async def med_delete(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    index = int(query.data.replace("med_del_", ""))
    meds = get_user_meds(chat_id)

    if 0 <= index < len(meds):
        med_name = meds[index]["name"]
        remove_med_jobs(context.application, chat_id, med_name)
        remove_user_med(chat_id, index)
        await query.edit_message_text(
            f"✅ {med_name} o'chirildi!\n\n🔄 /start bosib qaytadan boshlang."
        )
    else:
        await query.edit_message_text("⚠️ Dori topilmadi.")

    return ConversationHandler.END


async def med_name_input(update: Update, context) -> int:
    chat_id = update.message.chat_id
    user_data[chat_id] = {"med_name": update.message.text.strip()}

    keyboard = [
        [
            InlineKeyboardButton("1 marta", callback_data="med_freq_1"),
            InlineKeyboardButton("2 marta", callback_data="med_freq_2"),
        ],
        [
            InlineKeyboardButton("3 marta", callback_data="med_freq_3"),
            InlineKeyboardButton("4 marta", callback_data="med_freq_4"),
        ],
    ]
    await update.message.reply_text(
        f"✅ Dori: {user_data[chat_id]['med_name']}\n\n"
        "📌 Kuniga necha marta ichiladi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MED_FREQUENCY


async def med_frequency(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    freq = int(query.data.replace("med_freq_", ""))
    user_data[chat_id]["frequency"] = freq

    time_examples = {
        1: "Masalan: 09:00",
        2: "Masalan: 09:00 21:00",
        3: "Masalan: 08:00 14:00 21:00",
        4: "Masalan: 08:00 12:00 17:00 22:00",
    }

    await query.edit_message_text(
        f"✅ Kuniga {freq} marta\n\n"
        f"⏰ Qaysi vaqtlarda ichiladi? (24-soat formatda, probel bilan ajrating)\n"
        f"{time_examples.get(freq, '')}"
    )
    return MED_TIME


async def med_time_input(update: Update, context) -> int:
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    # Parse times
    times = []
    for part in text.split():
        part = part.strip()
        if ":" in part:
            try:
                h, m = map(int, part.split(":"))
                if 0 <= h <= 23 and 0 <= m <= 59:
                    times.append(f"{h:02d}:{m:02d}")
            except ValueError:
                pass

    if not times:
        await update.message.reply_text(
            "⚠️ Vaqt noto'g'ri formatda. Qaytadan yozing.\n"
            "Masalan: 09:00 21:00"
        )
        return MED_TIME

    user_data[chat_id]["times"] = times

    keyboard = [
        [
            InlineKeyboardButton("7 kun", callback_data="med_dur_7"),
            InlineKeyboardButton("14 kun", callback_data="med_dur_14"),
        ],
        [
            InlineKeyboardButton("30 kun", callback_data="med_dur_30"),
            InlineKeyboardButton("90 kun", callback_data="med_dur_90"),
        ],
    ]
    await update.message.reply_text(
        f"✅ Vaqtlar: {', '.join(times)}\n\n"
        "📅 Davolanish muddati qancha?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return MED_DURATION


async def med_duration(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    duration = int(query.data.replace("med_dur_", ""))
    user_data[chat_id]["duration"] = duration

    data = user_data[chat_id]
    med = {
        "name": data["med_name"],
        "frequency": data["frequency"],
        "times": data["times"],
        "duration": duration,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Save to file
    add_user_med(chat_id, med)

    # Schedule reminders
    schedule_med_reminders(context.application, chat_id, med)

    # Get AI info about the medication
    await query.edit_message_text("⏳ Dori haqida ma'lumot olinmoqda...")

    prompt = (
        f"Medication: {med['name']}\n"
        f"Dosage: {med['frequency']} times per day at {', '.join(med['times'])}\n"
        f"Duration: {med['duration']} days\n\n"
        f"Provide:\n"
        f"1. Brief description of this medication\n"
        f"2. Common side effects\n"
        f"3. Important warnings (food interactions, alcohol, driving)\n"
        f"4. Tips for taking it correctly\n\n"
        f"FORMATTING: No markdown (**, ##, ```). Plain text and emoji only.\n"
        f"Write section headers ending with colon.\n"
        f"Write in O'zbek language.\n"
        f"End with disclaimer: Bu AI tavsiyasi, shifokor maslahatini almashtirmaydi."
    )

    try:
        result = ai_request(
            "You are a pharmaceutical assistant. Provide medication information. "
            "Always include safety disclaimers. Write in O'zbek language.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik: {e}"

    times_str = ", ".join(med["times"])
    summary = (
        f"✅ DORI QO'SHILDI!\n\n"
        f"💊 Dori: {med['name']}\n"
        f"📊 Kuniga: {med['frequency']} marta\n"
        f"⏰ Vaqti: {times_str}\n"
        f"📅 Muddat: {med['duration']} kun\n"
        f"🔔 Eslatmalar faollashtirildi!\n\n"
    )

    await send_long_message(query.message, summary + result)
    await query.message.reply_text("🔄 /start bosib qaytadan boshlang.")
    user_data.pop(chat_id, None)
    return ConversationHandler.END


def restore_all_reminders(app):
    """Restore all scheduled reminders from saved data on bot startup."""
    data = load_med_data()
    count = 0
    for chat_id_str, meds in data.items():
        chat_id = int(chat_id_str)
        for med in meds:
            schedule_med_reminders(app, chat_id, med)
            count += 1
    if count:
        print(f"🔔 {count} ta eslatma tiklandi!")
