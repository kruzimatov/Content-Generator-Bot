# AI SMM Content Generator + Client Finder Bot

Telegram bot that generates professional SMM content and helps find clients using AI.

## Features

### 1. Content Generator
- Enter any niche (fitness, education, restaurants, etc.)
- Choose tone (sales, formal, informal, motivational)
- Choose platform (Instagram / Telegram)
- Get ready-to-use: post idea, full post, caption, and 10 hashtags

### 2. Client Finder + Auto DM
- Enter target niche and your service
- Provide client profile info (bio, posts, activity)
- Get: client analysis, 3 personalized DM variants, and follow-up message

## Tech Stack
- Python
- python-telegram-bot
- OpenAI API (GPT-4o-mini)

## Setup

1. Clone the repo
```bash
git clone https://github.com/kruzimatov/Content-Generator-Bot.git
cd Content-Generator-Bot
```

2. Install dependencies
```bash
pip install python-telegram-bot python-dotenv openai
```

3. Create `.env` file
```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
```

4. Run the bot
```bash
python3 bot.py
```

## Usage

Send `/start` to the bot and choose:
- **Content Generator** — for SMM posts
- **Client Finder + DM** — for outreach messages
