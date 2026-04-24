# AI Multi-Tool Telegram Bot

One Telegram bot with 6 AI-powered features built during AI Internship.

## Features

| # | Feature | File | Description |
|---|---------|------|-------------|
| 1 | Content Generator | `content_generator.py` | SMM post, caption, hashtag generation for Instagram/Telegram |
| 2 | Client Finder + DM | `client_finder.py` | Target client analysis and personalized cold DM writing |
| 3 | Resume Generator | `resume_generator.py` | AI resume with cover letter, PDF/DOCX export, photo, 3 templates |
| 4 | Med Reminder | `med_reminder.py` | Medication reminders, drug interaction checker, side effects info |
| 5 | Student Assistant | `student_assistant.py` | PDF/DOCX summary, notes, quiz, Q&A, translation, essay help |
| 6 | Taxi Driver | `taxi_driver.py` | Trip/fuel tracking, daily/weekly/monthly reports, AI advice |

## Project Structure

```
Content_Ai/
├── bot.py                  # Main entry point — menu + all handlers
├── utils.py                # Shared: AI request, markdown cleaner, message splitter
├── content_generator.py    # Feature 1
├── client_finder.py        # Feature 2
├── resume_generator.py     # Feature 3
├── med_reminder.py         # Feature 4
├── student_assistant.py    # Feature 5
├── taxi_driver.py          # Feature 6
├── .env                    # API keys (not in git)
├── med_data.json           # Auto-generated: medication storage
└── taxi_data.json          # Auto-generated: taxi trip/fuel storage
```

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
```

Get bot token from [@BotFather](https://t.me/BotFather) on Telegram.

### 4. Run the bot

```bash
python bot.py
```

## How to Use

1. Open your bot in Telegram
2. Send `/start` to see the main menu
3. Choose a feature by tapping a button
4. Follow the prompts
5. Send `/cancel` anytime to stop and go back

### Feature Details

**Content Generator**
- Enter niche → choose tone → choose platform → get ready-made post + caption + hashtags

**Client Finder + DM**
- Enter target niche → your service → client profile info → get analysis + 3 DM variants + follow-up

**Resume Generator**
- Enter name → job → experience → skills → send photo (optional) → choose template (Modern/Classic/Creative) → choose language (UZ/EN) → get resume as text + PDF + DOCX files

**Med Reminder**
- Add medication with schedule → bot sends reminders at set times
- Check drug interactions between your medications
- View all medications list
- Remove medications when course is done

**Student Assistant**
- Upload PDF or DOCX file → choose action:
  - Summary, Key Points, Lecture Notes, Quiz (10 questions), Ask a question, Translate (UZ/EN/RU), Essay help
- Can use multiple actions on the same document

**Taxi Driver**
- Log trips: `Chilonzor-Sergeli, 25000, 12` (route, price, km)
- Log fuel: `150000, 20` (price, liters)
- View daily/weekly/monthly reports with profit calculation
- Get AI advice on maximizing income

## Tech Stack

- **python-telegram-bot** — Telegram Bot API wrapper
- **OpenAI GPT-4o-mini** — AI text generation
- **fpdf2** — PDF file generation
- **python-docx** — Word DOCX file generation
- **PyMuPDF** — PDF text extraction
- **JSON** — lightweight data storage
