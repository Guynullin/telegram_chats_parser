import asyncio
from app_src.get_messages_from_chats import get_messages_from_chats
from app_src.merge_json import merge_json_files
from config import OUT_MERGED_JSON_DIR, ROOT_MESSAGES_DIR
from app_src.utils import setup_logger
import os
import sys
from pathlib import Path

logger = setup_logger('main')

async def async_main():
    logger.info('Starting parse messages')
    await get_messages_from_chats()

    logger.info('Starting merge json files')
    merge_json_files(ROOT_MESSAGES_DIR, OUT_MERGED_JSON_DIR)

    logger.info('End')

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()