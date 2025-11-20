import os
import re
import json
import pytz
import glob
import asyncio
import random

from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError, FloodWaitError
from tqdm import tqdm
from .utils import load_config, setup_logger
from config import ROOT_MESSAGES_DIR, MODE, LIMIT, SESSION_FILE

os.umask(0o002)

logger = setup_logger('message_parser')

MOSCOW_TZ = pytz.timezone('Europe/Moscow')

def sanitize_filename(name):
    """Sanitizes a filename by removing invalid characters.
    
    :param name: Original filename string
    :return: Sanitized filename string with invalid characters replaced by underscores
    """
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = name.strip().rstrip('.')
    return name

def moscow_now():
    """Returns current time in Moscow timezone.
    
    :return: Current datetime object with Moscow timezone
    """
    return datetime.now(MOSCOW_TZ)

def format_moscow_time(dt):
    """Formats datetime object to string in Moscow timezone.
    
    :param dt: Datetime object to format (naive or aware)
    :return: Formatted datetime string in Moscow timezone
    """
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt).astimezone(MOSCOW_TZ)
    else:
        dt = dt.astimezone(MOSCOW_TZ)
    return dt.strftime("%d-%m-%Y %H:%M:%S")

def parse_moscow_time(time_str):
    """Parses time string into datetime object with Moscow timezone.
    
    :param time_str: Time string in format "dd-mm-YYYY HH:MM:SS"
    :return: Datetime object with Moscow timezone
    """
    naive_dt = datetime.strptime(time_str, "%d-%m-%Y %H:%M:%S")
    return MOSCOW_TZ.localize(naive_dt)

class MessageParser:
    """Class for parsing and processing Telegram messages with rate limiting and progress tracking."""
    
    def __init__(self):
        """Initializes MessageParser with default settings."""
        self.request_count = 0
        self.request_limit = 5000
        self.base_delay = 0.1
        self.jitter = 0.1
        self.progress_bar = None

    async def random_delay(self):
        """Adds random delay between requests to avoid rate limiting.
        
        Updates progress bar with current delay information if available.
        """
        delay = self.base_delay + random.uniform(-self.jitter, self.jitter)
        await asyncio.sleep(max(0.1, delay))
        if self.progress_bar:
            self.progress_bar.set_postfix({"delay": f"{delay:.1f}s"})

    async def check_request_limit(self):
        """Checks if request limit has been reached and pauses if necessary.
        
        :return: True if limit was reached and pause occurred, False otherwise
        """
        self.request_count += 1
        if self.request_count >= self.request_limit:
            if self.progress_bar:
                original_desc = self.progress_bar.desc
                self.progress_bar.set_description("Request limit reached - pausing")
                self.progress_bar.refresh()
            
            await asyncio.sleep(3)
            self.request_count = 0
            
            if self.progress_bar:
                self.progress_bar.set_description(original_desc)
                self.progress_bar.refresh()
            return True
        return False

    def get_chat_file_path(self, category, chat_title):
        """Generates file path for storing chat messages.
        
        :param category: Category of the chat (used for directory structure)
        :param chat_title: Title of the chat (used for filename)
        :return: Full file path for the chat messages
        """
        sanitized_title = sanitize_filename(chat_title.replace(' ', '_'))
        return f"{ROOT_MESSAGES_DIR}/{category}/{sanitized_title}.json"

    def get_last_message_date(self, file_path):
        """Retrieves the date of the last message from a chat file.
        
        :param file_path: Path to the chat message file
        :return: Datetime object of the last message or None if file doesn't exist or is empty
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    messages = json.load(f)
                    if messages and isinstance(messages, list) and len(messages) > 0:
                        last_msg = messages[-1]
                        last_date_str = last_msg.get('date', '')
                        if last_date_str:
                            return parse_moscow_time(last_date_str)
                except json.JSONDecodeError:
                    logger.error(f"<get_last_message_date> File {file_path} is corrupted or has invalid format")
                    return None
        except Exception as e:
            logger.error(f"<get_last_message_date> Error reading last message from {file_path}: {str(e)}")
            
        return None

    def merge_and_sort_messages(self, existing_messages, new_messages):
        """Merges and sorts messages (oldest at the top, newest at the bottom).
        
        :param existing_messages: List of previously saved messages
        :param new_messages: List of newly parsed messages
        :return: Combined and sorted list of all messages
        """
        combined = existing_messages + new_messages
        combined.sort(key=lambda x: parse_moscow_time(x['date']))
        return combined

    async def parse_messages(self, client, chat_entity, category, mode='last_saved', limit=None):
        """Parses messages from a Telegram chat based on specified mode.
        
        :param client: TelegramClient instance
        :param chat_entity: Chat entity to parse messages from
        :param category: Category for organizing saved messages
        :param mode: Parsing mode ('last_saved', 'today', 'all', or 'count')
        :param limit: Maximum number of messages to parse (required for 'count' mode)
        :return: List of parsed message dictionaries
        """
        chat_title = getattr(chat_entity, 'title', 'chat')
        file_path = self.get_chat_file_path(category, chat_title)
        last_date = None
        messages_data = []
        
        if mode == 'last_saved':
            last_date = self.get_last_message_date(file_path)
            if not last_date:
                limit = limit or 5000  
        elif mode == 'today':
            today_start = MOSCOW_TZ.localize(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
            today_end = today_start + timedelta(days=1)
            last_date = self.get_last_message_date(file_path)
            
            if last_date and last_date >= today_start:
                pass  
            else:
                last_date = today_start  
            
            limit = limit
        elif mode == 'all':
            last_date = None
            limit = limit  
        elif mode == 'count':
            if not limit:
                raise ValueError("For 'count' mode, limit must be specified")
            last_date = self.get_last_message_date(file_path)
        else:
            raise ValueError(f"Unknown parsing mode: {mode}")
        
        try:
            if limit is not None:
                self.progress_bar = tqdm(
                    desc=f"Parsing {chat_title} ({mode})",
                    total=limit,
                    unit="msg",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
                )
            else:
                self.progress_bar = None
                logger.debug(f"<parse_messages> Started parsing {chat_title} ({mode}) without message limit")

            message_count = 0
            async for message in client.iter_messages(chat_entity, limit=None):  
                try:
                    await self.check_request_limit()
                    await self.random_delay()
                    
                    if not message or not hasattr(message, 'date'):
                        continue
                        
                    message_date = message.date.astimezone(MOSCOW_TZ)
                    
                    if mode == 'today':
                        if message_date < today_start:
                            logger.debug(f"<parse_messages> Reached start of day for {chat_title}")
                            break
                        if last_date and message_date <= last_date:
                            logger.debug(f"<parse_messages> Reached previously saved messages for {chat_title}")
                            break
                    elif last_date and message_date <= last_date:
                        logger.debug(f"<parse_messages> Reached previously saved messages for {chat_title}")
                        break
                        
                    if not message.sender:
                        continue
                        
                    message_text = message.text if message.text else ""
                    
                    message_data = {
                        "date": format_moscow_time(message.date),
                        "sender_id": message.sender.id if message.sender else None,
                        "sender_username": getattr(message.sender, 'username', None),
                        "text": message_text[:500]
                    }
                    
                    if message_data["text"] or message_data["sender_id"]:
                        messages_data.insert(0, message_data)  
                    
                    message_count += 1
                    if self.progress_bar:
                        self.progress_bar.update(1)
                        self.progress_bar.set_postfix({
                            "last": message_text[:20] + "...",
                            "delay": f"{self.base_delay:.1f}s"
                        })
                    
                    if limit is not None and message_count >= limit:
                        logger.debug(f"<parse_messages> Reached specified message limit ({limit}) for {chat_title}")
                        break
                        
                except Exception as e:
                    logger.error(f"<parse_messages> Error processing message (ID: {getattr(message, 'id', 'unknown')}): {str(e)}")
                    continue
                    
        except FloodWaitError as e:
            if self.progress_bar:
                self.progress_bar.set_description(f"⚠️ FloodWait {e.seconds}s")
            await asyncio.sleep(e.seconds)
            return await self.parse_messages(client, chat_entity, category, mode, limit)
        except Exception as e:
            logger.error(f"<parse_messages> Error fetching messages: {str(e)}")
        finally:
            if self.progress_bar:
                self.progress_bar.close()
                self.progress_bar = None
        
        return messages_data

    def get_first_message_date(self, file_path):
        """Retrieves the date of the first (oldest) message from a chat file.
        
        :param file_path: Path to the chat message file
        :return: Datetime object of the first message or None if file doesn't exist or is empty
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line.startswith('['):
                    while True:
                        line = f.readline()
                        if line.startswith('{'):
                            try:
                                msg = json.loads(line.rstrip().rstrip(','))
                                return parse_moscow_time(msg['date'])
                            except (json.JSONDecodeError, KeyError):
                                continue
        except Exception as e:
            logger.error(f"<get_first_message_date> Error reading first message from {file_path}: {str(e)}")
            
        return None

def merge_and_sort_messages(existing_messages, new_messages):
    """Merges and sorts messages (oldest at the top, newest at the bottom).
    
    :param existing_messages: List of previously saved messages
    :param new_messages: List of newly parsed messages
    :return: Combined and sorted list of all messages
    """
    combined = existing_messages + new_messages
    combined.sort(key=lambda x: parse_moscow_time(x['date']))
    return combined

def save_messages(messages, file_path, append=False):
    """Saves messages to file with optional appending to existing file.
    
    :param messages: List of message dictionaries to save
    :param file_path: Path to save messages to
    :param append: Whether to append to existing file (False overwrites)
    :return: Path where messages were saved
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if messages:
        messages.sort(key=lambda x: parse_moscow_time(x['date']))
    
    if append and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_messages = json.load(f)
                except json.JSONDecodeError:
                    existing_messages = []
            
            all_messages = existing_messages + messages
            all_messages.sort(key=lambda x: parse_moscow_time(x['date']))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_messages, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"<save_messages> Error appending to file {file_path}: {str(e)}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    
    os.chmod(file_path, 0o664) 
    return file_path

async def process_chat_file(client, parser, file_path, mode='last_saved', limit=1000):
    """Processes a single chat file with specified parsing mode.
    
    :param client: TelegramClient instance
    :param parser: MessageParser instance
    :param file_path: Path to file containing chat links
    :param mode: Parsing mode ('last_saved', 'today', 'all', or 'count')
    :param limit: Maximum number of messages to parse (required for 'count' mode)
    :return: Tuple of (processed_chats_count, updated_files_count)
    """
    category = os.path.splitext(os.path.basename(file_path))[0]
    logger.info(f"<process_chat_file> Starting processing file: {file_path} (Category: {category}, Mode: {mode})")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chat_links = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"<process_chat_file> Error reading file {file_path}: {str(e)}")
        return 0, 0
    
    processed_chats = 0
    updated_files = 0
    
    for chat_link in chat_links:
        try:
            logger.debug(f"<process_chat_file> Processing chat: {chat_link}")
            chat = await client.get_entity(chat_link)
            chat_title = sanitize_filename(chat.title.replace(' ', '_'))
            
            messages = await parser.parse_messages(client, chat, category, mode, limit)
            
            if messages:
                file_path = parser.get_chat_file_path(category, chat_title)
                append = mode in ['last_saved', 'today', 'count'] and os.path.exists(file_path)
                saved_path = save_messages(messages, file_path, append)
                updated_files += 1
                logger.info(f"<process_chat_file> Saved {len(messages)} messages to {saved_path}")
            else:
                logger.debug("<process_chat_file> No new messages to save")
            
            processed_chats += 1
            await asyncio.sleep(10)
            
        except ChannelPrivateError:
            logger.error(f"<process_chat_file> Chat is private: {chat_link}")
        except Exception as e:
            logger.error(f"<process_chat_file> Error processing chat {chat_link}: {str(e)}")
    
    logger.info(f"<process_chat_file> Finished processing category {category}. Processed chats: {processed_chats}, updated files: {updated_files}")
    return processed_chats, updated_files

async def get_messages_from_chats():
    """Main function to retrieve messages from Telegram chats based on configuration."""
    config = load_config()
    
    if not os.path.exists('session_name.session'):
        raise Exception("Session file not found! Absolute path: " + os.path.abspath('session_name.session'))
    
    client = TelegramClient(
        SESSION_FILE,
        config['api_id'],
        config['api_hash'],
    )
    
    await client.start()
    
    total_processed = 0
    total_updated = 0

    parser = MessageParser()
    input_files = glob.glob('data/*.txt')
    
    if not input_files:
        logger.error("<get_messages_from_chats> No chat files found in data/ directory")
        await client.disconnect()
        return
    
    
    for file_path in input_files:
        processed, updated = await process_chat_file(client, parser, file_path, mode=MODE, limit=LIMIT)
        total_processed += processed
        total_updated += updated
    
    logger.info(f"<get_messages_from_chats> Summary: Processed files: {len(input_files)}, chats: {total_processed}, updated files: {total_updated}")
    await client.disconnect()