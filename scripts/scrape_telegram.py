# src/scraper/telegram_scraper.py

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from loguru import logger

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")


# Root output paths
RAW_MESSAGES_DIR = Path("data/raw/telegram_messages")
RAW_MEDIA_DIR = Path("data/raw/telegram_media")

# List of channels to scrape
CHANNELS = {
    # "lobelia4cosmetics": "https://t.me/lobelia4cosmetics",
    # "tikvahpharma": "https://t.me/tikvahpharma",
    "CheMeds" : 'https://t.me/CheMeds',
    "medicalethiopia" : 'https://t.me/medicalethiopia',
    "tenamereja" : 'https://t.me/tenamereja'
}


async def scrape_channel(channel_name: str, channel_url: str, limit=200):
    logger.info(f"Scraping channel: {channel_name}")
    today = datetime.now().strftime("%Y-%m-%d")

    # Folder for messages
    msg_output_dir = RAW_MESSAGES_DIR / today
    msg_output_dir.mkdir(parents=True, exist_ok=True)

    # Folder for media
    media_output_dir = RAW_MEDIA_DIR / today / channel_name
    media_output_dir.mkdir(parents=True, exist_ok=True)

    # File for messages
    msg_file_path = msg_output_dir / f"{channel_name}.json"

    async with TelegramClient('scraping_session', API_ID, API_HASH) as client:
        messages = []

        async for msg in client.iter_messages(channel_url, limit=limit):
            data = {
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "message": msg.message,
                "sender_id": msg.sender_id,
                "has_media": msg.media is not None,
                "media_type": type(msg.media).__name__ if msg.media else None,
                "file": None,
            }

            if isinstance(msg.media, MessageMediaPhoto):
                media_path = media_output_dir / f"{channel_name}_{msg.id}.jpg"
                await client.download_media(msg, file=media_path)
                data["file"] = str(media_path)

            messages.append(data)

        with open(msg_file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    logger.success(f"{channel_name}: {len(messages)} messages scraped.")


async def run_scraper():
    for name, url in CHANNELS.items():
        try:
            await scrape_channel(name, url)
        except Exception as e:
            logger.error(f"Failed to scrape {name}: {e}")


if __name__ == "__main__":
    asyncio.run(run_scraper())