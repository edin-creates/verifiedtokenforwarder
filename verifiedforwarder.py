import os
import re
import asyncio
import logging
from telethon import TelegramClient, events
from dotenv import load_dotenv
from ethsourcecode import get_etherscan_url, filter_links, get_contract_source_code
from caextractor import extract_contract_address

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#env variables used
load_dotenv()
api_id = os.environ['API_ID']
api_hash = os.environ['API_HASH']
bot_token = os.environ['BOT_TOKEN']
source_channel = os.environ['SOURCE_CHANNEL']
target_channel = os.environ['TARGET_CHANNEL']


async def main():
    async with TelegramClient("anon1", api_id, api_hash) as client:
        @client.on(events.NewMessage(chats=source_channel))
        async def my_event_handler(event):
            message = event.message
            message_text = message.text
            logger.info(f"message text: {message_text}")

            if "Verified:" in message_text:
                logger.info("Found a verified contract message")
                contract_address = extract_contract_address(message_text)

                if contract_address:
                    logger.info(
                        f"Extracted contract address: {contract_address}")
                    etherscan_url = get_etherscan_url(contract_address)
                    source_code_lines = get_contract_source_code(
                        contract_address)

                    filtered_lines = filter_links(source_code_lines)
                    source_code_excerpt = "\n".join(filtered_lines)

                    # Remove everything below the _ character in the message text
                    message_text = re.sub(
                        r"_.*", "", message_text, flags=re.DOTALL)
                    message_text += f"\n\n{source_code_excerpt}\n\n{etherscan_url}"

            await client.send_message(target_channel, message_text, link_preview=False)
            logger.info("Forwarded message to target channel")

        logger.info("Bot is running...")
        await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
