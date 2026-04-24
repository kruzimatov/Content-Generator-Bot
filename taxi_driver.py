import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from utils import ai_request, send_long_message

# Conversation states
TAXI_MENU, TAXI_TRIP, TAXI_FUEL, TAXI_REPORT = range(50, 54)

# Persistent storage
DATA_FILE = os.path.join(os.path.dirname(__file__), "taxi_data.json")

# User data for conversation flow
user_data = {}


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_driver(chat_id: int) -> dict:
    data = load_data()
    key = str(chat_id)
    if key not in data:
        data[key] = {"trips": [], "fuel": []}
        save_data(data)
    return data[key]


def add_trip(chat_id: int, trip: dict):
    data = load_data()
    key = str(chat_id)
    if key not in data:
        data[key] = {"trips": [], "fuel": []}
    data[key]["trips"].append(trip)
    save_data(data)


def add_fuel(chat_id: int, fuel: dict):
    data = load_data()
    key = str(chat_id)
    if key not in data:
        data[key] = {"trips": [], "fuel": []}
    data[key]["fuel"].append(fuel)
    save_data(data)


def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")


def filter_by_date(items: list, days: int) -> list:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [i for i in items if i.get("date", "") >= cutoff]


# --- Menu ---

async def taxi_menu(message, edit=False):
    keyboard = [
        [
            InlineKeyboardButton("🚗 Safar qo'shish", callback_data="taxi_add_trip"),
            InlineKeyboardButton("⛽ Benzin yozish", callback_data="taxi_add_fuel"),
        ],
        [
            InlineKeyboardButton("📊 Bugungi hisob", callback_data="taxi_today"),
            InlineKeyboardButton("📈 Haftalik", callback_data="taxi_weekly"),
        ],
        [
            InlineKeyboardButton("📅 Oylik hisobot", callback_data="taxi_monthly"),
            InlineKeyboardButton("🧠 AI maslahat", callback_data="taxi_ai"),
        ],
    ]
    text = (
        "🚕 TAXI HAYDOVCHI YORDAMCHI\n\n"
        "🚗 Safar qo'shish — yangi buyurtma kiritish\n"
        "⛽ Benzin yozish — yoqilg'i xarajati\n"
        "📊 Bugungi hisob — kunlik daromad\n"
        "📈 Haftalik — 7 kunlik statistika\n"
        "📅 Oylik hisobot — 30 kunlik tahlil\n"
        "🧠 AI maslahat — foydani oshirish uchun tavsiyalar"
    )
    if edit:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def taxi_action(update: Update, context) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    action = query.data

    if action == "taxi_add_trip":
        await query.edit_message_text(
            "🚗 YANGI SAFAR\n\n"
            "Quyidagi formatda yozing:\n"
            "manzil, narx, masofa(km)\n\n"
            "Masalan:\n"
            "Chilonzor-Sergeli, 25000, 12\n\n"
            "Yoki qisqacha:\n"
            "25000, 12"
        )
        return TAXI_TRIP

    elif action == "taxi_add_fuel":
        await query.edit_message_text(
            "⛽ BENZIN XARAJATI\n\n"
            "Quyidagi formatda yozing:\n"
            "summa, litr\n\n"
            "Masalan:\n"
            "150000, 20"
        )
        return TAXI_FUEL

    elif action == "taxi_today":
        await _show_report(query.message, chat_id, days=1, title="BUGUNGI HISOB")
        return TAXI_MENU

    elif action == "taxi_weekly":
        await _show_report(query.message, chat_id, days=7, title="HAFTALIK HISOBOT")
        return TAXI_MENU

    elif action == "taxi_monthly":
        await _show_report(query.message, chat_id, days=30, title="OYLIK HISOBOT")
        return TAXI_MENU

    elif action == "taxi_ai":
        await _ai_advice(query.message, chat_id)
        return TAXI_MENU

    return TAXI_MENU


async def taxi_trip_input(update: Update, context) -> int:
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    parts = [p.strip() for p in text.split(",")]

    try:
        if len(parts) >= 3:
            route = parts[0]
            price = int(parts[1])
            distance = float(parts[2])
        elif len(parts) == 2:
            route = "Noma'lum"
            price = int(parts[0])
            distance = float(parts[1])
        else:
            raise ValueError("Format noto'g'ri")
    except (ValueError, IndexError):
        await update.message.reply_text(
            "⚠️ Format noto'g'ri. Qaytadan yozing:\n"
            "manzil, narx, masofa\n"
            "Masalan: Chilonzor-Sergeli, 25000, 12"
        )
        return TAXI_TRIP

    trip = {
        "date": get_today_str(),
        "time": datetime.now().strftime("%H:%M"),
        "route": route,
        "price": price,
        "distance": distance,
    }
    add_trip(chat_id, trip)

    await update.message.reply_text(
        f"✅ Safar qo'shildi!\n\n"
        f"📍 Yo'nalish: {route}\n"
        f"💰 Narx: {price:,} so'm\n"
        f"📏 Masofa: {distance} km\n"
        f"🕐 Vaqt: {trip['time']}"
    )
    await taxi_menu(update.message, edit=False)
    return TAXI_MENU


async def taxi_fuel_input(update: Update, context) -> int:
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    parts = [p.strip() for p in text.split(",")]

    try:
        price = int(parts[0])
        liters = float(parts[1])
    except (ValueError, IndexError):
        await update.message.reply_text(
            "⚠️ Format noto'g'ri. Qaytadan yozing:\n"
            "summa, litr\n"
            "Masalan: 150000, 20"
        )
        return TAXI_FUEL

    fuel = {
        "date": get_today_str(),
        "price": price,
        "liters": liters,
    }
    add_fuel(chat_id, fuel)

    await update.message.reply_text(
        f"✅ Benzin xarajati yozildi!\n\n"
        f"💰 Summa: {price:,} so'm\n"
        f"⛽ Litr: {liters} L\n"
        f"📊 1 litr narxi: {price / liters:,.0f} so'm"
    )
    await taxi_menu(update.message, edit=False)
    return TAXI_MENU


async def _show_report(message, chat_id: int, days: int, title: str):
    driver = get_driver(chat_id)
    trips = filter_by_date(driver["trips"], days)
    fuels = filter_by_date(driver["fuel"], days)

    if not trips and not fuels:
        await message.reply_text(
            f"📊 {title}\n\n"
            "Ma'lumot topilmadi. Avval safar yoki benzin qo'shing."
        )
        await taxi_menu(message, edit=False)
        return

    total_income = sum(t["price"] for t in trips)
    total_distance = sum(t["distance"] for t in trips)
    total_fuel_cost = sum(f["price"] for f in fuels)
    total_liters = sum(f["liters"] for f in fuels)
    net_profit = total_income - total_fuel_cost
    trip_count = len(trips)

    avg_per_trip = total_income // trip_count if trip_count else 0
    avg_per_km = total_income / total_distance if total_distance else 0
    fuel_per_km = total_fuel_cost / total_distance if total_distance else 0

    # Find most popular route
    routes = {}
    for t in trips:
        r = t["route"]
        if r != "Noma'lum":
            routes[r] = routes.get(r, 0) + 1
    top_route = max(routes, key=routes.get) if routes else "—"

    # Find most profitable route
    route_income = {}
    for t in trips:
        r = t["route"]
        if r != "Noma'lum":
            route_income[r] = route_income.get(r, 0) + t["price"]
    best_route = max(route_income, key=route_income.get) if route_income else "—"

    report = (
        f"📊 {title}\n"
        f"{'=' * 30}\n\n"
        f"🚗 Safarlar soni: {trip_count}\n"
        f"📏 Umumiy masofa: {total_distance:,.1f} km\n\n"
        f"💰 DAROMAD:\n"
        f"   Umumiy: {total_income:,} so'm\n"
        f"   O'rtacha/safar: {avg_per_trip:,} so'm\n"
        f"   O'rtacha/km: {avg_per_km:,.0f} so'm\n\n"
        f"⛽ XARAJAT:\n"
        f"   Benzin: {total_fuel_cost:,} so'm\n"
        f"   Litr: {total_liters:,.1f} L\n"
        f"   Benzin/km: {fuel_per_km:,.0f} so'm\n\n"
        f"💵 SOF FOYDA: {net_profit:,} so'm\n\n"
        f"📍 Eng ko'p yo'nalish: {top_route}\n"
        f"💎 Eng foydali yo'nalish: {best_route}"
    )

    await message.reply_text(report)
    await taxi_menu(message, edit=False)


async def _ai_advice(message, chat_id: int):
    driver = get_driver(chat_id)
    trips = filter_by_date(driver["trips"], 30)
    fuels = filter_by_date(driver["fuel"], 30)

    if not trips:
        await message.reply_text(
            "⚠️ AI maslahat uchun kamida bir necha safar kerak.\n"
            "Avval safarlarni kiriting."
        )
        await taxi_menu(message, edit=False)
        return

    total_income = sum(t["price"] for t in trips)
    total_distance = sum(t["distance"] for t in trips)
    total_fuel = sum(f["price"] for f in fuels)
    trip_count = len(trips)

    routes_summary = {}
    for t in trips:
        r = t["route"]
        if r not in routes_summary:
            routes_summary[r] = {"count": 0, "income": 0, "distance": 0}
        routes_summary[r]["count"] += 1
        routes_summary[r]["income"] += t["price"]
        routes_summary[r]["distance"] += t["distance"]

    routes_text = "\n".join(
        f"  {r}: {d['count']} safar, {d['income']:,} so'm, {d['distance']:.1f} km"
        for r, d in routes_summary.items()
    )

    await message.reply_text("⏳ AI tahlil qilmoqda...")

    prompt = (
        f"You are a taxi business consultant. Analyze this driver's data:\n\n"
        f"Last 30 days stats:\n"
        f"- Total trips: {trip_count}\n"
        f"- Total income: {total_income:,} so'm\n"
        f"- Total distance: {total_distance:.1f} km\n"
        f"- Total fuel cost: {total_fuel:,} so'm\n"
        f"- Net profit: {total_income - total_fuel:,} so'm\n"
        f"- Avg per trip: {total_income // trip_count if trip_count else 0:,} so'm\n\n"
        f"Routes breakdown:\n{routes_text}\n\n"
        f"Give practical advice:\n"
        f"1. DAROMAD TAHLILI - bugungi holat qanday?\n"
        f"2. ENG FOYDALI YO'NALISHLAR - qaysi marshrut eng yaxshi?\n"
        f"3. YOQILG'I TEJASH - qanday tejash mumkin?\n"
        f"4. DAROMADNI OSHIRISH - aniq tavsiyalar\n"
        f"5. BO'SH VAQTNI KAMAYTIRISH - qachon ko'proq ishlash kerak?\n\n"
        f"FORMATTING: No markdown (**, ##, ```). Plain text and emoji. "
        f"Section headers ending with colon. Write in O'zbek language."
    )

    try:
        result = ai_request(
            "You are a taxi business consultant. Give practical, data-driven advice. Write in O'zbek language.",
            prompt,
        )
    except Exception as e:
        result = f"❌ Xatolik: {e}"

    await send_long_message(message, result)
    await taxi_menu(message, edit=False)
