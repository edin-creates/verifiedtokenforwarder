import os
import re
import asyncio
import logging
from telethon import TelegramClient, events
from dotenv import load_dotenv
from modules import ethsourcecode
from modules import  caextractor
from urlextract import URLExtract
import requests
from web3 import Web3
from moralis import evm_api
import os
from datetime import datetime
from bs4 import BeautifulSoup
import time
import random
import concurrent.futures
import sqlite3
import pymongo
from pymongo import MongoClient, IndexModel, ASCENDING
import json
from telethon.extensions import markdown
from telethon import types
from modules import asynciohopanalysis

MAX_RETRIES = 3
MIN_DELAY = 0.3
MAX_DELAY = 1.5





logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#env variables used
load_dotenv()

ETHERSCAN_API_KEY = os.environ['ETHERSCAN_API_KEY']
ETHERSCAN_API_KEY2 = os.environ['ETHERSCAN_API_KEY2']
ETHERSCAN_API_KEY3 = os.environ['ETHERSCAN_API_KEY3']
proxy = os.environ['PROXY1']

api_id = os.environ['API_ID']
api_hash = os.environ['API_HASH']
bot_token = os.environ['BOT_TOKEN']
source_channel = int(os.environ['SOURCE_CHANNEL'])
target_verified = int(os.environ['TARGET_CHANNEL_VERIFIED'])
target_deployed = int(os.environ['TARGET_CHANNEL_DEPLOYED'])
target_longlock = int(os.environ['TARGET_CHANNEL_LONGLOCKS'])
target_burn = int(os.environ['TARGET_CHANNEL_BURN'])

mongodbusername = os.environ['mongodbUsername']
mongodbpassword = os.environ['mongodbPassword']


#custom markdown to use custom telgram emojis with telethon
class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities
    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)

# MongoDb database manager class that handles connections to the tokens database
class DatabaseManager:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['tokenDatabase']
        self.tokens = self.db['tokens']
        self.create_indexes()
        
    def create_indexes(self):
        # Create indexes for the specified fields
        index1 = IndexModel([("deployer_address", ASCENDING)])
        index2 = IndexModel([("pastcoin_data", ASCENDING)])
        index3 = IndexModel([("hop_analysis", ASCENDING)])
        index4 = IndexModel([("events.deployed.timestamp", ASCENDING)])
        index5 = IndexModel([("events.verified.timestamp", ASCENDING)])
        index6 = IndexModel([("events.locked.timestamp", ASCENDING)])
        index7 = IndexModel([("events.burned.timestamp", ASCENDING)])
        self.tokens.create_indexes([index1, index2, index3, index4, index5, index6, index7])
        
    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

# Define the URI for connecting to your MongoDB instance
uri = f"mongodb://{mongodbusername}:{mongodbpassword}@localhost:27017/tokenDatabase?authSource=tokenDatabase"

# Create an instance of DatabaseManager with the URI
database_manager = DatabaseManager(uri)

# Access the tokens collection from anywhere in your app
tokens = database_manager.tokens



#function that gets the ca from message_text from itoken tg and does all the work, made it a function because its reused around 4 times and takes a lot of space it gets confusing
def remove_excess_text(text):
    idx = text.find("—", text.find("[Deployer]"))
    if idx != -1:
        return text[:idx]
    return text

#extracts the deployer address from the itoken messages
def extract_deployer_address(text):

    cleaned_text = re.sub(r"[^a-zA-Z0-9\s:]", "", text)
    print(cleaned_text)
    contract_address = None
    pattern = r"(?i)Deployerhttps:etherscanioaddress\s*(0x[a-fA-F0-9]{40})"
    match = re.search(pattern, cleaned_text)

    if match:
        contract_address = match.group(1)
        # web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
        # checksum_address = web3.to_checksum_address(contract_address)

    return contract_address

def extract_token_metadata(message):
    #extracts from an itoken post the token's metadata
    pair = None, None
    token_symbol = None
    token_name = None
    total_supply = None

    #get the pair address if it exists
    pair_address_pattern = r"(dexscreener\.com/ethereum/)(0x[a-fA-F0-9]{40})"
    # Search for contract addresses directly attached to specific URLs
    match_attached = re.search(pair_address_pattern, message)
    if match_attached:
        pair = (match_attached.group(2), pair[1])
        print(f"Pair Address : {pair}")

        
    # Extracting the token name and symbol
    token_match = re.search( r'\*\*\s*(?:Verified|Burned|Deployed|Locked):\s*\*\*\s+([^(]+)\s+\((.+?)\)', message)
    if token_match:
        token_symbol = token_match.group(1)
        token_name = token_match.group(2)  # Assuming symbols are uppercase
        print("Token Name:", token_name)
        print("Token Symbol:", token_symbol)

    # Extracting Uni version (Uni V2 or Uni V3)
    uni_version_match = re.search(r'\*\*\s*Pair:\s*\*\* .*?(Uni V\d+)', message)
    if uni_version_match:
        uni_version = uni_version_match.group(1)
        pair = (pair[0], uni_version)
        print("Uni Version:", uni_version)
    

    # Extracting supply and decimals
    supply_match = re.search(r'\*\*\s*Supply:\s*\*\* (.+?) \(\+(\d+) decimals\)', message)
    if supply_match:
        total_supply = supply_match.group(1)
        total_supply = int(total_supply.replace(',', ''))
        decimals = int(supply_match.group(2))
        # message = re.sub(r'\*\*\s*Supply:\s*\*\* (.+?) \(\+(\d+) decimals\)', "", message)
        print("Total Supply:", total_supply)
        print("Decimals:", decimals)
    return pair, token_name, token_symbol, total_supply, decimals
    


# function that gets an itoken message text and generates an address data
def treatment_message_text(message_text, tokens):
    contract_address = caextractor.extract_contract_address(message_text)

    if contract_address:
        
        logger.info(
            f"Extracted contract address: {contract_address}")
        
        query = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
        token_data = tokens.find_one(query)
        # If token_data is not None, access the pastcoin_data field
        if token_data:
            pastcoins = token_data.get("pastcoin_data", "No pastcoin_data field found.")
            deployer_address = token_data.get("deployer_address", None)
            print(pastcoins)
        else:
            print(f"No data found for contract address: {contract_address}")
        if deployer_address is None:
            deployer_address= ethsourcecode.get_deployer(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
        # balance_eth, deployer_age = get_deployer_details(contract_address)
        balance_eth = ethsourcecode.get_balance(deployer_address, f"{ETHERSCAN_API_KEY2}", None, None)
        if balance_eth is not None:
            round_balance_eth = round( balance_eth, 3)
        deployer_age = ethsourcecode.get_age(deployer_address, f"{ETHERSCAN_API_KEY3}", None, None)            

        # Define a function for each API call
        def task1():
            for _ in range(3):  # Retry up to 3 times
                try:
                    return ethsourcecode.get_address_nametag(deployer_address, proxy)
                except Exception as e:
                    print(f"Error in task1: {e}")
                    time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

        def task2():
            for _ in range(3):  # Retry up to 3 times
                try:
                    return ethsourcecode.get_marketcap(contract_address)
                except Exception as e:
                    print(f"Error in task2: {e}")
                    time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

        def task3():
            for _ in range(3):  # Retry up to 3 times
                try:
                    return ethsourcecode.extract_nametags_and_addresses(deployer_address, proxy)
                except Exception as e:
                    print(f"Error in task3: {e}")
                    time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

        def task4():
            for _ in range(3):  # Retry up to 3 times
                try:
                    return ethsourcecode.get_socialmedia_filter(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
                except Exception as e:
                    print(f"Error in task4: {e}")
                    time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying
        
        def task5():
            for _ in range(3):  # Retry up to 3 times
                try:
                    return ethsourcecode.detect_liquidity_removals(deployer_address, f"{ETHERSCAN_API_KEY2}", None, None)
                except Exception as e:
                    print(f"Error in task4: {e}")
                    time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

        
        # Create a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the tasks to the executor manually
            task1_future = executor.submit(task1)
            task2_future = executor.submit(task2)
            task3_future = executor.submit(task3)
            task4_future = executor.submit(task4)
            task5_future = executor.submit(task5)
            
            # Initialize the variables
            deployer_name = None
            mcap, liquidity = None, None
            cexfunded = None
            telegram_links, twitter_links,discord_links, other_websites, medium_links, docs_links, app_links, moar_links,triple_links, social_media_text = None, None, None, None, None, None, None, None, None, None
            tx_lpremove, number_lpremove = None,  None
            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed([task1_future, task2_future, task3_future, task4_future, task5_future]):
                try:
                    result = future.result()  # Get the result of the task
                    #print(f"Task completed with result: {result}")

                    # Store the result back into the appropriate variable
                    if future == task1_future:
                        deployer_name = result
                    elif future == task2_future:
                        mcap, liquidity = result
                    elif future == task3_future:
                        cexfunded = result
                    elif future == task4_future:
                        telegram_links, twitter_links,discord_links, other_websites, medium_links, docs_links, app_links, moar_links,triple_links, social_media_text = result
                    elif future == task5_future:
                        number_lpremove, tx_lpremove = result

                except Exception as e:
                    print(f"Exception occurred during task execution: {e}")


        try:                        
           if int(pastcoins[3]) > 0:
               addy = pastcoins[0]
               past_name, past_symbol = ethsourcecode.get_name_symbol(addy)
               contracts_deployed_count = pastcoins[2]
        except ValueError:
           print(f"Error: Unable to convert {pastcoins[3]} to an integer.")

        #get the pair address if it exists
        pair_address_pattern = r"(dexscreener\.com/ethereum/)(0x[a-fA-F0-9]{40})"
        # Search for contract addresses directly attached to specific URLs
        match_attached = re.search(pair_address_pattern, message_text)
        if match_attached:
            pair = match_attached.group(2)
            print(f"Pair Address : {pair}")
        # Extracting Uni version (Uni V2 or Uni V3)
        uni_version_match = re.search(r'\*\*\s*Pair:\s*\*\* .*?(Uni V\d+)', message_text)
        if uni_version_match:
            uni_version = uni_version_match.group(1)
            print("Uni Version:", uni_version)

        
        if "Supply" in message_text:
            message_text = re.sub(r"\*\*\s*Supply:.*", "", message_text, flags=re.DOTALL)
        else:
            message_text = re.sub(r"☎️.*", "", message_text)
    
        message_text = re.sub(r"\*\*\s*Pair.*", "", message_text)
        lines = message_text.splitlines()
        filtered_lines = [line for line in lines if  line.strip() != ""]
        
        message_text = '\n'.join(filtered_lines)

        # Add an emoji before "CA:"
        message_text = message_text.replace("**CA:**", "[✍️](emoji/5816736498883498308) **CA:**")
        #Add a chart link
        if pair[0]:
            message_text += f"\n[📈](emoji/5823476741384967483) [Screener](https://dexscreener.com/ethereum/{pair})"+"[▶️](emoji/5827885422235095225)"+f"[Dext](https://www.dextools.io/app/ether/pair-explorer/{pair})"

        ##############################################################
        
        if mcap is not None:
            message_text += f"\n\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n[▶️](emoji/5816812219156927426)  [📈](emoji/5823242158861193696) **Marketcap:**  `{mcap}`\n[▶️](emoji/5816812219156927426) [💧](emoji/5823394089034322747) **Liquidity:**  `{liquidity}`\n"

        if social_media_text.strip(): 
            message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n [🌐](emoji/5821458708051267544) **SOCIAL LINKS** [🌐](emoji/5821458708051267544)\n{social_media_text}"
        ##############################################################

        message_text +=f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n[🚀](emoji/5823193307903168922) **DEPLOYER DETAILS:** [🚀](emoji/5823193307903168922)\n"
        if deployer_name is not None:
            message_text += f"      [▶️](emoji/5816812219156927426)  ⚡️ **Nametag:**  `{deployer_name}`\n"
        
        if len(cexfunded)>0 :
            message_text += f"      [▶️](emoji/5816812219156927426) [🔹](emoji/5816477795823392378) **Cex:** `{cexfunded}`\n"

        if balance_eth is not None:
            message_text += f"      [▶️](emoji/5816812219156927426)  [💰](emoji/5816636675253605227) **Balance:**  `{round_balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426)  [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"
        else:
            message_text += f"      [▶️](emoji/5816812219156927426) [💰](emoji/5816636675253605227) **Balance:**  `{balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426)  [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"
        from modules import asynciohopanalysis
        if number_lpremove is not None:
            if number_lpremove > 0 :
                result_lpremove = asynciohopanalysis.process_shorten_and_link_element(tx_lpremove)
                message_text += f"  [▶️](emoji/5816812219156927426)  🛑 **liq remove Txs** : `{number_lpremove}` \n     [▶️](emoji/5816812219156927426) {result_lpremove} \n"

        if int(pastcoins[1]) != 0:
            message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN**`(out of {contracts_deployed_count})`\n       [▶️](emoji/5816812219156927426)** Name:** `{past_name}` \n       [▶️](emoji/5816812219156927426) ** Symbol:** `{past_symbol}` \n      [▶️](emoji/5816812219156927426) [✍️](emoji/5816736498883498308) ** Ca:** `{pastcoins[0]}` \n     [▶️](emoji/5816812219156927426) 🎯 **ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
        elif int(pastcoins[2]) > 0: #checks if no ath mcap data is available but there is a high tx past coin
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n      [▶️](emoji/5816812219156927426) ** Name:** `{past_name}` \n      [▶️](emoji/5816812219156927426) ** Symbol:** `{past_symbol}` \n      [▶️](emoji/5816812219156927426) [✍️](emoji/5816736498883498308)** Ca:** `{pastcoins[0]}` \n "

        return message_text, contract_address

##### IMAGES##### global cached media variable that stores the file with the images to use for all the posts
cached_media = [None, None, None, None]


#Main
async def main():
    global cached_media
    # Get the message containing the image
    deployed_image_id = 742 
    verified_image_id = 753
    locked_image_id = 749
    burned_image_id = 751
    called_image_id = 741


    async with TelegramClient("ubuntusession1", api_id, api_hash) as client:

        #retrieving the image files if not cached
        source_chat = 1962610706  # Replace with the chat or channel where the image is located
        if cached_media[0] is None:
            print("deployed image not cached yet...")
            message = await client.get_messages(source_chat, ids=deployed_image_id)
            cached_media[0] = message.media.photo

        if cached_media[1] is None:
            print("verified image not cached yet...")

            message = await client.get_messages(source_chat, ids=verified_image_id)
            cached_media[1] = message.media.photo
        
        if cached_media[2] is None:
            print("locked image not cached yet...")

            message = await client.get_messages(source_chat, ids=locked_image_id)
            cached_media[2] = message.media.photo
        
        if cached_media[3] is None:
            print("burned image not cached yet...")

            message = await client.get_messages(source_chat, ids=burned_image_id)
            cached_media[3] = message.media.photo

        #listening to the events from the source channel telegram
        @client.on(events.NewMessage(chats=source_channel))
        async def my_event_handler(event):
            start = time.time()
            message = event.message
            message_text = " \n[🔹](emoji/5816477795823392378)\n\u00A0\n"+message.text
            logger.info(f"message text: {message_text}")
            client.parse_mode = CustomMarkdown()

            ##############################################################################################################
            ##############################################################################################################
            ##############################################################################################################
            #freshly deployed tokens #####################################################################################
            if "Deployed" in message_text: # and "🛑" not in message_text:
                
                logger.info("Found a verified contract message")
                print("Indexes created successfully!")
                contract_address = caextractor.extract_contract_address(message_text)

                if contract_address:
                    logger.info(
                        f"Extracted contract address: {contract_address}")
                    
                    # basically we try extracting the deployer address just from the text, if it fails then we go back to xthe api calls
                    round_balance_eth = None
                    deployer_address = extract_deployer_address(message_text)
                    print(f"extracted from message deployer: {deployer_address}")
                    pair, token_name, token_symbol, total_supply, decimals = extract_token_metadata(message_text)

                    
                    if deployer_address is None:
                        deployer_address, balance_eth, deployer_age = ethsourcecode.get_deployer_details(contract_address, f"{ETHERSCAN_API_KEY3}", None, None)
                        if balance_eth is not None:
                            round_balance_eth = float(round( balance_eth, 3))
                    else:
                        balance_eth = ethsourcecode.get_balance(deployer_address, f"{ETHERSCAN_API_KEY}", None, None)
                        deployer_age = ethsourcecode.get_age(deployer_address, f"{ETHERSCAN_API_KEY2}", None, None)
                        if balance_eth is not None:
                            round_balance_eth = float(round( balance_eth, 3))

                    deployer_name = ethsourcecode.get_address_nametag(deployer_address, proxy)
                    cexfunded = ethsourcecode.extract_nametags_and_addresses(deployer_address, proxy)
                    number_lpremove, tx_lpremove = ethsourcecode.detect_liquidity_removals(deployer_address, f"{ETHERSCAN_API_KEY3}", None, None)
                    
                    #get the pastcoins if there is anything interesting
                    pastcoins = ethsourcecode.fpc(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
                    
                    if int(pastcoins[3]) > 0:
                        addy = pastcoins[0]
                        past_name, past_symbol = ethsourcecode.get_name_symbol(addy)
                        contracts_deployed_count = pastcoins[2]

                    # get the social media urls organised from the source code
                    telegram_links, twitter_links,discord_links, other_websites, medium_links, docs_links, app_links, moar_links,triple_links, social_media_text = ethsourcecode.get_socialmedia_filter(contract_address, f"{ETHERSCAN_API_KEY2}", None, None)
                    

                   
                    
                    if "Supply" in message_text:
                        message_text = re.sub(r"\*\*\s*Supply:.*", "", message_text, flags=re.DOTALL)
                    else:
                        message_text = re.sub(r"☎️.*", "", message_text)
                
                    message_text = re.sub(r"\*\*\s*Pair.*", "", message_text)
                    lines = message_text.splitlines()
                    filtered_lines = [line for line in lines if  line.strip() != ""]
                    
                    message_text = '\n'.join(filtered_lines)

                    # Add an emoji before "CA:" and "Suplly"
                    message_text = message_text.replace("**CA:**", "[✍️](emoji/5816736498883498308) **CA:**")
                    #Add a chart link
                    if pair[0]:
                        message_text += f"\n[📈](emoji/5823476741384967483) [Screener](https://dexscreener.com/ethereum/{pair})"+"[▶️](emoji/5827885422235095225)"+f"[Dext](https://www.dextools.io/app/ether/pair-explorer/{pair})"
                    
                    #message_text += f"---------------------------------\n** ⟹💲 Marketcap:**  `{mcap}`\n** ⟹💰 Liquidity:**  `{liquidity}`\n"

                    if social_media_text.strip(): 
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n [🌐](emoji/5821458708051267544) **SOCIAL LINKS** [🌐](emoji/5821458708051267544)  \n{social_media_text}"
                    ##############################################################

                    message_text +=f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n[🚀](emoji/5823193307903168922) **DEPLOYER DETAILS:** [🚀](emoji/5823193307903168922)\n"
                    if deployer_name is not None:
                        message_text += f"      [▶️](emoji/5816812219156927426) ** ⚡️ Nametag:**  `{deployer_name}`\n"
                    
                    if len(cexfunded)>0 :
                        message_text += f"      [▶️](emoji/5816812219156927426) [🔹](emoji/5816477795823392378) **Cex:** `{cexfunded}`\n"
                    if balance_eth is not None:
                        message_text += f"      [▶️](emoji/5816812219156927426) [💰](emoji/5816636675253605227) **Balance:**  `{round_balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426)  [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"
                    else:
                        message_text += f"      [▶️](emoji/5816812219156927426) [💰](emoji/5816636675253605227) **Balance:**  `{balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426) [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"


                    if number_lpremove is not None:
                        if number_lpremove > 0 :
                            result_lpremove = asynciohopanalysis.process_shorten_and_link_element(tx_lpremove)
                            message_text += f"      [▶️](emoji/5816812219156927426) **  🛑 liq remove Txs** : `{number_lpremove}` \n     [▶️](emoji/5816812219156927426) {result_lpremove} \n"
                    
                    if pastcoins[1] != 0: #checks if one ath Mcap past ca at least exists
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n      [▶️](emoji/5816812219156927426)** Name:** `{past_name}` \n       [▶️](emoji/5816812219156927426) ** Symbol:** `{past_symbol}` \n      [▶️](emoji/5816812219156927426) [✍️](emoji/5816736498883498308)** Ca:** `{pastcoins[0]}` \n      [▶️](emoji/5816812219156927426)** 🎯 ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
                    elif int(pastcoins[2]) > 0: #checks if no ath mcap data is available but there is a high tx past coin
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n      [▶️](emoji/5816812219156927426)** Name:** `{past_name}` \n       [▶️](emoji/5816812219156927426) ** Symbol:** `{past_symbol}` \n      [▶️](emoji/5816812219156927426)** Ca:** `{pastcoins[0]}` \n "
                    
                    try:
                        # Send the message and capture the returned Message object
                        sent_message = await client.send_file(target_deployed, file=cached_media[0], caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)
                    except Exception as e:
                        messagex = await client.get_messages(source_chat, ids=deployed_image_id)
                        cached_media[0] = messagex.media.photo
                        sent_message = await client.send_file(target_deployed, file=cached_media[0], caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id
                    timestamp_utc = sent_message.date
                    print(f"\n telegram deployed forwarder finished in: {round(time.time() - start, 2)} seconds \n")
                    
                    
                    #Mongo db add document with data

                    # Sample data
                    
                    filter_ = {"_id": contract_address.lower()}
                    update_ = {
                        "$setOnInsert": {
                            "token_name": token_name,
                            "token_symbol": token_symbol,
                            "pair": {
                                "address": pair[0],
                                "uniswap_version": pair[1]
                            },
                            "total_supply": total_supply,
                            "decimals": decimals,
                            "deployer_address": deployer_address,
                            "deployer_age": deployer_age,
                            "deployer_balance": round_balance_eth,
                            "deployer_name": deployer_name,
                            "cexfunded": cexfunded,
                            "liquidity_removals": number_lpremove,
                            "pastcoin_data": pastcoins,
                            "social_media": None,
                            "hop_message": None,
                            "hop_analysis": None,
                            "events": {
                                "deployed": {
                                    "timestamp": timestamp_utc,
                                    "message_id": message_id,
                                    "message_text": message_text
                                },
                                "verified": {},
                                "locked": {},
                                "burned": {}
                            }
                        }
                    }

                    # Update the document in MongoDB, or insert it if it doesn't exist
                    tokens.update_one(filter_, update_, upsert=True)


                    logger.info("Forwarded message to target channel")
            
            #Verified Tokens ################################################################################
            if "Verified" in message_text: # and "🛑" not in message_text:
                logger.info("Found a verified contract message")         

                contract_address = caextractor.extract_contract_address(message_text)
                pair, token_name, token_symbol, total_supply, decimals = extract_token_metadata(message_text)
                hopanalysis = None
                
                if contract_address:
                    
                    logger.info(
                        f"Extracted contract address: {contract_address}")
                    ###########################################

                    # Fetch the document
                    query = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
                    token_data = tokens.find_one(query)
                    print(f"\n\nmongodb database tokendata {token_data}\n\n")
                    # If token_data is not None, access the pastcoin_data field
                    
                    if token_data is not None:
                        pastcoins = token_data.get("pastcoin_data", "No pastcoin_data field found.")
                        deployer_address = token_data.get("deployer_address", None)
                        hopanalysis_secondary = token_data.get("hop_analysis")
                        if isinstance(hopanalysis_secondary, dict):
                            hopanalysis = hopanalysis_secondary.get("hop_message", None)

                        print(pastcoins)
                    else:
                        print(f"No data found for contract address: {contract_address}")
                        deployer_address = extract_deployer_address(message_text)
                        pastcoins = ethsourcecode.fpc(deployer_address, f"{ETHERSCAN_API_KEY}", None, None)

                    if deployer_address:
                        if deployer_address is None:
                            deployer_address= ethsourcecode.get_deployer(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
                        print(f"deployer address is: {deployer_address}")
                    else:
                        deployer_address = ethsourcecode.get_deployer(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
                    # balance_eth, deployer_age = get_deployer_details(contract_address)
                    balance_eth = ethsourcecode.get_balance(deployer_address, f"{ETHERSCAN_API_KEY}", None, None)
                    if balance_eth is not None:
                        round_balance_eth = round( balance_eth, 3)
                    deployer_age = ethsourcecode.get_age(deployer_address, f"{ETHERSCAN_API_KEY}", None, None)            

                    # Define a function for each API call
                    def task1():
                        for _ in range(3):  # Retry up to 3 times
                            try:
                                return ethsourcecode.get_address_nametag(deployer_address, proxy)
                            except Exception as e:
                                print(f"Error in task1: {e}")
                                time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

                    def task2():
                        for _ in range(3):  # Retry up to 3 times
                            try:
                                return ethsourcecode.get_marketcap(contract_address)
                            except Exception as e:
                                print(f"Error in task2: {e}")
                                time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

                    def task3():
                        for _ in range(3):  # Retry up to 3 times
                            try:
                                return ethsourcecode.extract_nametags_and_addresses(deployer_address, proxy)
                            except Exception as e:
                                print(f"Error in task3: {e}")
                                time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

                    def task4():
                        for _ in range(3):  # Retry up to 3 times
                            try:
                                return ethsourcecode.get_socialmedia_filter(contract_address, f"{ETHERSCAN_API_KEY3}", None, None)
                            except Exception as e:
                                print(f"Error in task4: {e}")
                                time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

                    def task5():
                        for _ in range(3):  # Retry up to 3 times
                            try:
                                return ethsourcecode.detect_liquidity_removals(deployer_address, f"{ETHERSCAN_API_KEY2}", None, None)
                            except Exception as e:
                                print(f"Error in task5: {e}")
                                time.sleep(random.uniform(0.3, 1.5))  # Wait for a random time before retrying

                    # Create a ThreadPoolExecutor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # Submit the tasks to the executor manually
                        task1_future = executor.submit(task1)
                        task2_future = executor.submit(task2)
                        task3_future = executor.submit(task3)
                        task4_future = executor.submit(task4)
                        task5_future = executor.submit(task5)

                        
                        # Initialize the variables
                        deployer_name = None
                        mcap, liquidity = None, None
                        cexfunded = None
                        telegram_links, twitter_links,discord_links, other_websites, medium_links, docs_links, app_links, moar_links,triple_links, social_media_text = None, None, None, None, None, None, None, None, None, None
                        number_lpremove, tx_lpremove = None, None
                        # Wait for all tasks to complete
                        for future in concurrent.futures.as_completed([task1_future, task2_future, task3_future, task4_future, task5_future]):
                            try:
                                result = future.result()  # Get the result of the task
                                #print(f"Task completed with result: {result}")

                                # Store the result back into the appropriate variable
                                if future == task1_future:
                                    deployer_name = result
                                elif future == task2_future:
                                    mcap, liquidity = result
                                elif future == task3_future:
                                    cexfunded = result
                                elif future == task4_future:
                                    telegram_links, twitter_links,discord_links, other_websites, medium_links, docs_links, app_links, moar_links,triple_links, social_media_text = result
                                elif future == task5_future:
                                    number_lpremove, tx_lpremove = result
                                    print(f"numbe of lp removals: {number_lpremove}")

                            except Exception as e:
                                print(f"Exception occurred during task execution: {e}")


                    print(f"pastcoins before potential verified int error: {pastcoins} ")            
                    if int(pastcoins[3]) > 0:
                        addy = pastcoins[0]
                        past_name, past_symbol = ethsourcecode.get_name_symbol(addy)
                        contracts_deployed_count = pastcoins[2]
                    

                    #traitement de texte, short clean message post
                    if "Supply" in message_text:
                        message_text = re.sub(r"\*\*\s*Supply:.*", "", message_text, flags=re.DOTALL)
                    else:
                        message_text = re.sub(r"☎️.*", "", message_text)
                
                    message_text = re.sub(r"\*\*\s*Pair.*", "", message_text)
                    lines = message_text.splitlines()
                    filtered_lines = [line for line in lines if  line.strip() != ""]
                    
                    message_text = '\n'.join(filtered_lines)

                    # Add an emoji before "CA:" and "Suplly"
                    message_text = message_text.replace("**CA:**", "[✍️](emoji/5816736498883498308) **CA:**")
                    #Add a chart link
                    if pair[0]:
                        message_text += f"\n[📈](emoji/5823476741384967483) [Screener](https://dexscreener.com/ethereum/{pair}) [▶️](emoji/5827885422235095225) [Dext](https://www.dextools.io/app/ether/pair-explorer/{pair})"


                    ##############################################################
                    
                    if mcap is not None:
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n [▶️](emoji/5816812219156927426) [📈](emoji/5823242158861193696) **Marketcap:**  `{mcap}`\n [▶️](emoji/5816812219156927426) [💧](emoji/5823394089034322747) **Liquidity:**  `{liquidity}`\n"

                    if social_media_text.strip(): 
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n [🌐](emoji/5821458708051267544) **SOCIAL LINKS** [🌐](emoji/5821458708051267544)  \n{social_media_text}"
                    ##############################################################

                    message_text +=f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n[🚀](emoji/5823193307903168922) **DEPLOYER DETAILS:** [🚀](emoji/5823193307903168922)\n"
                    if deployer_name is not None:
                        message_text += f"      [▶️](emoji/5816812219156927426) **⚡️ Nametag:**  `{deployer_name}`\n"
                    
                    if len(cexfunded)>0 :
                        message_text += f"      [▶️](emoji/5816812219156927426) [🔹](emoji/5816477795823392378) **Cex:** `{cexfunded}`\n"

                    if balance_eth is not None:
                        message_text += f"      [▶️](emoji/5816812219156927426) [💰](emoji/5816636675253605227) **Balance:**  `{round_balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426)  [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"
                    else:
                        message_text += f"      [▶️](emoji/5816812219156927426) [💰](emoji/5816636675253605227) **Balance:**  `{balance_eth}` **ETH**\n      [▶️](emoji/5816812219156927426) [🕰](emoji/5821312773652484635) **Age:**  `{deployer_age}` **days**\n"

                    if number_lpremove is not None and number_lpremove>0 :
                        result_lpremove = asynciohopanalysis.process_shorten_and_link_element(tx_lpremove)
                        message_text += f"      [▶️](emoji/5816812219156927426) ** 🛑 liq remove Txs** : `{number_lpremove}` \n       {result_lpremove} \n"
                    
                    if pastcoins[1] != 0:
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n      [▶️](emoji/5816812219156927426)** Name:** `{past_name}` \n       [▶️](emoji/5816812219156927426)**  Symbol:** `{past_symbol}` \n      [▶️](emoji/5816812219156927426) [✍️](emoji/5816736498883498308) **Ca:** `{pastcoins[0]}` \n      [▶️](emoji/5816812219156927426)** 🎯 ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
                    elif int(pastcoins[2]) > 0:
                        message_text += f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n      [▶️](emoji/5816812219156927426)** Name:** `{past_name}` \n       [▶️](emoji/5816812219156927426)** Symbol:** `{past_symbol}` \n       [▶️](emoji/5816812219156927426) [✍️](emoji/5816736498883498308)**Ca:** `{pastcoins[0]}` \n "

                    if hopanalysis is not None:
                        if hopanalysis != "":
                            message_text += f"{hopanalysis}"

                    

                    try:
                        sent_message = await client.send_file(target_verified, file= cached_media[1] , caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)
                    except Exception as e:
                        messagex = await client.get_messages(source_chat, ids=deployed_image_id)
                        cached_media[1] = messagex.media.photo
                        sent_message = await client.send_file(target_verified, file= cached_media[1] , caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)

                    print(f"\n telegram verified forwarder finished in: {round(time.time() - start, 2)} seconds \n")

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id
                    timestamp_utc = sent_message.date

                    extension = ethsourcecode.check_website_extension(other_websites)
                    # Define the filter and the update
                    
                    filter_ = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
                    update_ = {
                        "$set": {
                            "pair": {
                                "address": pair[0],
                                "uniswap_version": pair[1]
                            },
                            "events.verified": {
                                "timestamp": timestamp_utc,
                                "message_id": message_id,
                                "message_text": message_text
                            },
                            "social_media": {
                                "telegram": telegram_links,
                                "twitter": twitter_links,
                                "websites": other_websites,
                                "medium": medium_links,
                                "discord": discord_links,
                                "docs": docs_links,
                                "apps": app_links,
                                "moar": moar_links,
                                "extension": extension,
                                "triple": triple_links
                            }

                        }
                    }

                    # Use upsert=True to insert if not exists, or update if exists
                    tokens.update_one(filter_, update_, upsert=True)




                    logger.info("Forwarded message to target channel")
            
            
            ###############################################################################################
            #Burned Tokens ################################################################################
            if "burned" in message_text: # and "🛑" not in message_text:
                logger.info("Found a verified contract message")
                pair, token_name, token_symbol, total_supply, decimals = extract_token_metadata(message_text)

                message_text, contract_address = treatment_message_text(message_text, tokens)    

                try:
                    sent_message = await client.send_file(target_burn, file = cached_media[3] , caption= message_text, parse_mode=CustomMarkdown(), link_preview=False)
                except Exception as e:
                    messagex = await client.get_messages(source_chat, ids=deployed_image_id)
                    cached_media[3] = messagex.media.photo
                    sent_message = await client.send_file(target_burn, file = cached_media[3] , caption= message_text, parse_mode=CustomMarkdown(), link_preview=False)

                # Now, you can access the message ID using sent_message.id
                message_id = sent_message.id

                timestamp_utc = sent_message.date

                # Define the filter and the update
                
                filter_ = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
                update_ = {
                    "$set": {
                        "pair": {
                                "address": pair[0],
                                "uniswap_version": pair[1]
                            },
                        "events.burned": {
                            "timestamp": timestamp_utc,
                            "message_id": message_id,
                            "message_text": message_text
                        }
                    }
                }

                # Use upsert=True to insert if not exists, or update if exists
                tokens.update_one(filter_, update_, upsert=True)
                print(f"\n telegram burn forwarder finished in: {round(time.time() - start, 2)} seconds \n")
                logger.info("Forwarded message to target channel")


            ###########################################################################################
            #Check for a long lock ############################################################
            match = re.search(r"locked for (\d+) days", message_text)
            if match:
                days = int(match.group(1))
                if days > 180: # and "🛑" not in message_text:
                    logger.info("Found a Long Lock contract message")
                
                    message_text, contract_address = treatment_message_text(message_text, tokens)
                    pair, token_name, token_symbol, total_supply, decimals = extract_token_metadata(message_text)


                    try:
                        sent_message = await client.send_file(target_longlock, file = cached_media[2] , caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)
                    except Exception as e:
                        messagex = await client.get_messages(source_chat, ids=deployed_image_id)
                        cached_media[2] = messagex.media.photo
                        sent_message = await client.send_file(target_longlock, file = cached_media[2] , caption = message_text, parse_mode=CustomMarkdown(), link_preview=False)

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id

                    timestamp_utc = sent_message.date

                    # Define the filter and the update
                    
                    filter_ = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
                    update_ = {
                        "$set": {
                            "pair": {
                                "address": pair[0],
                                "uniswap_version": pair[1]
                            },
                            "events.locked": {
                                "timestamp": timestamp_utc,
                                "message_id": message_id,
                                "message_text": message_text
                            }
                        }
                    }

                    # Use upsert=True to insert if not exists, or update if exists
                    tokens.update_one(filter_, update_, upsert=True)
                    print(f"\n telegram long lock forwarder finished in: {round(time.time() - start, 2)} seconds \n")
                    logger.info("Forwarded message to target channel")
            

        logger.info("Bot is running...")
        await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
