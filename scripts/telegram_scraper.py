# import asyncio
# import os
# import json
# import logging
# from datetime import datetime
# from telethon import TelegramClient
# from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
# from dotenv import load_dotenv
# from pathlib import Path
#
#
# class TelegramScraper:
#     def __init__(self, message_limit=1000):
#         # Load credentials
#         load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
#         self.api_id = int(os.getenv('API_ID'))
#         self.api_hash = os.getenv('API_HASH')
#         self.message_limit = message_limit
#         self.client = None
#
#         os.makedirs("logs", exist_ok=True)
#         logging.basicConfig(filename="logs/scrape_log.txt", level=logging.INFO)
#
#     async def init_client(self):
#         self.client = TelegramClient('scraping_session', self.api_id, self.api_hash)
#         await self.client.start()
#
#     async def scrape_channel(self, channel_username):
#         try:
#             entity = await self.client.get_entity(channel_username)
#             channel_name = entity.username or entity.title.replace(' ', '_')
#             print(f"🔍 Scraping: {channel_username} → {channel_name}")
#
#             message_groups = {}  # Key = message date, value = list of messages
#
#             async for message in self.client.iter_messages(entity, limit=self.message_limit):
#                 # Skip system messages
#                 if not message.message and not message.media:
#                     continue
#
#                 msg_dict = message.to_dict()
#                 msg_dict['text'] = message.message or ""
#                 msg_dict['has_media'] = bool(message.media)
#
#                 # Extract message date (not scrape date)
#                 msg_date = message.date.strftime('%Y-%m-%d')
#
#                 # Save media if present
#                 if message.media:
#                     media_dir = f"data/raw/media/{msg_date}/{channel_name}"
#                     os.makedirs(media_dir, exist_ok=True)
#                     filename = f"{message.id}"
#                     if isinstance(message.media, MessageMediaPhoto):
#                         file_path = os.path.join(media_dir, f"{filename}.jpg")
#                         await self.client.download_media(message.media, file_path)
#                         msg_dict['downloaded_media'] = file_path
#                     elif isinstance(message.media, MessageMediaDocument):
#                         ext = message.file.ext or '.bin'
#                         file_path = os.path.join(media_dir, f"{filename}{ext}")
#                         await self.client.download_media(message.media, file_path)
#                         msg_dict['downloaded_media'] = file_path
#
#                 # Add to date-grouped message list
#                 message_groups.setdefault(msg_date, []).append(msg_dict)
#
#             total_count = 0
#
#             # Save messages grouped by message date
#             for msg_date, msgs in message_groups.items():
#                 save_dir = f"data/raw/telegram_messages/{msg_date}"
#                 os.makedirs(save_dir, exist_ok=True)
#                 json_path = os.path.join(save_dir, f"{channel_name}.json")
#
#                 with open(json_path, 'w', encoding='utf-8') as f:
#                     json.dump(msgs, f, ensure_ascii=False, indent=2)
#
#                 logging.info(f"[{msg_date}] ✅ Saved {len(msgs)} messages from {channel_username}")
#                 print(f"✅ Saved {len(msgs)} messages for {channel_name} on {msg_date}")
#                 total_count += len(msgs)
#
#             print(f"✅ Finished scraping {channel_username} ({total_count} total messages)")
#
#         except Exception as e:
#             logging.error(f"[{datetime.now()}] ❌ Error scraping {channel_username}: {str(e)}")
#             print(f"❌ Error scraping {channel_username}: {e}")
#
#     async def scrape_channels(self, channels):
#         await self.init_client()
#         async with self.client:
#             for channel in channels:
#                 await self.scrape_channel(channel)
#
#     def run_scraper(self, channels):
#         asyncio.run(self.scrape_channels(channels))
#
#
# if __name__ == "__main__":
#     # You can change this list or load from a file
#     channels = [
#         'https://t.me/lobelia4cosmetics',
#         'https://t.me/tikvahpharma',
#         'https://t.me/chemedchannel',
#         'https://t.me/medicalethiopia',
#         'https://t.me/Thequorachannel',
#         'https://t.me/tenamereja',
#         'https://t.me/HakimApps_Guideline',
#         'https://t.me/CheMeds'
#     ]
#     scraper = TelegramScraper(message_limit=500)
#     scraper.run_scraper(channels)
#

# src/telegram_scraper.py

import asyncio
import os
import json
import logging
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv
import time
import random


class TelegramScraper:
    def __init__(self, message_limit=10000,rate_limit_delay=1.0):
        load_dotenv('../.env')
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')

        if not all([self.api_id, self.api_hash]):
            raise ValueError("API_ID and API_HASH must be set in the .env file")

        self.client = TelegramClient('scraping_session', self.api_id, self.api_hash)
        self.rate_limit_delay = rate_limit_delay  # seconds between message fetches
        self.message_limit = message_limit
        self.setup_logging()

    def setup_logging(self):
        log_path = os.path.join('..', 'logs', 'scraping.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    async def init_client(self):
        await self.client.start()

    async def scrape_channel(self, channel_username, base_output_dir, base_media_dir):
        try:
            entity = await self.client.get_entity(channel_username)
            channel_name = entity.username or channel_username.strip('@')
            logging.info(f"Scraping started for channel: {channel_name}")

            messages_data = []
            async for message in self.client.iter_messages(entity, limit=10000):
                msg_date = message.date.strftime('%Y-%m-%d')
                channel_dir = os.path.join(base_output_dir, msg_date)
                os.makedirs(channel_dir, exist_ok=True)

                media_path = None
                if message.media:
                    media_folder = os.path.join(base_media_dir, msg_date, channel_name)
                    os.makedirs(media_folder, exist_ok=True)

                    if hasattr(message.media, 'photo'):
                        media_filename = f"{channel_name}_{message.id}.jpg"
                        media_path = os.path.join(media_folder, media_filename)
                        await self.client.download_media(message.media, media_path)

                    elif hasattr(message.media, 'document') and message.file:
                        media_filename = f"{channel_name}_{message.id}_{message.file.name}"
                        media_path = os.path.join(media_folder, media_filename)
                        await self.client.download_media(message.media, media_path)

                messages_data.append({
                    'channel_title': entity.title,
                    'channel_username': channel_username,
                    'message_id': message.id,
                    'message': message.message,
                    'date': message.date.isoformat(),
                    'media_path': media_path
                })

                # ⏱️ Rate limit delay
                await asyncio.sleep(self.rate_limit_delay + random.uniform(0, 0.5))

            output_path = os.path.join(base_output_dir, msg_date, f"{channel_name}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)

            logging.info(f"Finished scraping {channel_name} ({len(messages_data)} messages)")

        except FloodWaitError as e:
            logging.warning(f"Rate limited on {channel_username}. Sleeping for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            await self.scrape_channel(channel_username, base_output_dir, base_media_dir)
        except Exception as e:
            logging.error(f"❌ Error scraping {channel_username}: {str(e)}")

    async def scrape_channels(self, channels, output_dir, media_dir):
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(media_dir, exist_ok=True)

        await self.init_client()
        async with self.client:
            for channel in channels:
                await self.scrape_channel(channel, output_dir, media_dir)
                # ⏱️ Add pause between channel scrapes to avoid hitting hard limits
                await asyncio.sleep(5 + random.uniform(0, 3))

    def run_scraper(self, channels, output_dir, media_dir):
        asyncio.run(self.scrape_channels(channels, output_dir, media_dir))


if __name__ == "__main__":
    channels = [
        '@lobelia4cosmetics',
        '@tikvahpharma',
        '@chemedchannel'
        # Add more from et.tgstat.com/medicine
    ]

    base_output_dir = '../data/raw/telegram_messages'
    base_media_dir = '../data/raw/media'

    scraper = TelegramScraper(message_limit=500,rate_limit_delay=1.5)  # Set delay between messages
    scraper.run_scraper(channels, base_output_dir, base_media_dir)