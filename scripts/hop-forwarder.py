import requests
import httpx
import logging
import re
import concurrent.futures
import time
import random
from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime
from modules import ethsourcecode, caextractor
from scripts import forwarder
from modules import asynciohopanalysis
from telethon import TelegramClient, events
import asyncio
from aiolimiter import AsyncLimiter
import web3
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from itertools import cycle
import sqlite3
import json
import pymongo
from pymongo import MongoClient, IndexModel, ASCENDING


load_dotenv()
ETHERSCAN_API_KEY1 = os.environ['ETHERSCAN_API_KEY']
ETHERSCAN_API_KEY2 = os.environ['ETHERSCAN_API_KEY2'] # goes with proxy 2 and UA 2
ETHERSCAN_API_KEY3 = os.environ['ETHERSCAN_API_KEY3'] # goes with proxy 3 and UA 3
ETHERSCAN_API_KEY4 = os.environ['HOPANALYSIS_ETHERSCAN_1'] #goes with proxy 4 and UA 4
ETHERSCAN_API_KEY5 = os.environ['HOPANALYSIS_ETHERSCAN_2'] #goes with proxy 5 and UA 5
ETHERSCAN_API_KEY6 = os.environ['HOPANALYSIS_ETHERSCAN_3'] #goes with proxy 5 and UA 5
ETHERSCAN_API_KEY7 = os.environ['ETHERSCAN_EREN1'] #goes with proxy 1 and UA 1
ETHERSCAN_API_KEY8 = os.environ['ETHERSCAN_EREN2']
ETHERSCAN_API_KEY9 = os.environ['ETHERSCAN_EREN3']
ETHERSCAN_API_KEY10 = os.environ['ETHERSCAN_API_KEY10'] #goes with proxy 1 and UA 1
ETHERSCAN_API_KEY11 = os.environ['ETHERSCAN_API_KEY11']
ETHERSCAN_API_KEY12 = os.environ['ETHERSCAN_API_KEY12']



INFURA_API_KEY = os.environ['INFURA_API_KEY']
INFURA_API_KEY2 = os.environ['INFURA_API_KEY2']
INFURA_API_KEY3 = os.environ['INFURA_API_KEY3']
INFURA_API_KEY4 = os.environ['INFURA_API_KEY4']
INFURA_API_KEY5 = os.environ['INFURA_API_KEY5']
INFURA_API_KEY6 = os.environ['INFURA_API_KEY6']
INFURA_API_KEY7 = os.environ['INFURA_API_KEY7']
INFURA_API_KEY8 = os.environ['INFURA_API_KEY8']
INFURA_API_KEY9 = os.environ['INFURA_API_KEY9']


INFURA_URL = os.environ['INFURA_URL']
ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
MOBULA_API_KEY = os.environ['MOBULA_API_KEY']
MORALIS_API_KEY1 = os.environ['MORALIS_API_KEY_1']
MORALIS_API_KEY2 = os.environ['MORALIS_API_KEY_2']
MORALIS_API_KEY3 = os.environ['MORALIS_API_KEY_3']
MORALIS_API_KEY4 = os.environ['MORALIS_API_KEY_4']


#USER AGENTS
USER_AGENT1 = os.environ['USER_AGENT1']
USER_AGENT2 = os.environ['USER_AGENT2']
USER_AGENT3 = os.environ['USER_AGENT3']
USER_AGENT4 = os.environ['USER_AGENT4']
USER_AGENT5 = os.environ['USER_AGENT5']
USER_AGENT6 = os.environ['USER_AGENT6']

#PROXY
PROXY1 = os.environ['PROXY1']
PROXY2 = os.environ['PROXY2']
PROXY3 = os.environ['PROXY3']
PROXY4 = os.environ['PROXY4']
PROXY5 = os.environ['PROXY5']
PROXY6 = os.environ['PROXY6']
PROXY7 = os.environ['PROXY7']
PROXY8 = os.environ['PROXY8']
PROXY9 = os.environ['PROXY9']
PROXY10 = os.environ['PROXY10']



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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)


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

    def get_token_data(self, contract_address):
        """
        Retrieve data for a specific token by contract address.
        
        :param contract_address: The contract address of the token.
        :return: The data for the token, or None if no matching token was found.
        """
        return self.tokens.find_one({"_id": contract_address})
        
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




#Main
async def main():
    async with TelegramClient("hopanalysis", api_id, api_hash) as clientTG:
        @clientTG.on(events.NewMessage(chats=target_deployed))
        async def my_event_handler(event):
            start = time.time()
            message = event.message
            message_text = message.text
            logger.info(f"message text: {message_text}")


            #freshly deployed tokens #####################################################################################
            if "Deployed" in message_text and "🛑" not in message_text:
                logger.info("Found a verified contract message")
                contract_address = caextractor.extract_contract_address(message_text)
                if contract_address:
                    logger.info(
                        f"Extracted contract address: {contract_address}")
                    # We Try extracting the deployer address just from the text, if it fails then use our api functions
                    deployer_address = forwarder.extract_deployer_address(message_text)
                    print(f"extracted from message deployer: {deployer_address}")
                    if deployer_address is None:
                        deployer_address = ethsourcecode.get_deployer(contract_address, f"{ETHERSCAN_API_KEY3}", None, None)

                    async with httpx.AsyncClient() as client:
                        # Define your API keys, proxies, and headers
                        api_keys = [f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY5}", f"{ETHERSCAN_API_KEY6}", f"{ETHERSCAN_API_KEY7}",f"{ETHERSCAN_API_KEY8}",f"{ETHERSCAN_API_KEY9}",f"{ETHERSCAN_API_KEY12}", f"{ETHERSCAN_API_KEY10}",f"{ETHERSCAN_API_KEY11}"]
                        
                        #proxies setup in clients
                        proxies = [f"{PROXY1}", f"{PROXY2}", f"{PROXY3}", f"{PROXY4}", f"{PROXY5}", f"{PROXY6}", f"{PROXY7}", f"{PROXY8}", f"{PROXY9}", f"{PROXY10}", None]
                        
                        #headers setup in clients
                        headers = [f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT5}", f"{USER_AGENT6}",f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}",f"{USER_AGENT2}", f"{USER_AGENT3}"]
                        
                        #infura api key
                        infuras = [f"{INFURA_API_KEY}", f"{INFURA_API_KEY4}",f"{INFURA_API_KEY7}",f"{INFURA_API_KEY2}", f"{INFURA_API_KEY5}",f"{INFURA_API_KEY8}",f"{INFURA_API_KEY3}", f"{INFURA_API_KEY6}",f"{INFURA_API_KEY9}",f"{INFURA_API_KEY3}", f"{INFURA_API_KEY6}",f"{INFURA_API_KEY9}"]


                        # Create a list of dictionaries, where each dictionary represents a client
                        clients = [asynciohopanalysis.CustomClient(headers={"User-Agent": user_agent}, proxies={"http://": proxy, "https://": proxy}, api_key=api_key, infuras=infuras) for user_agent, proxy, api_key, infuras in zip(headers, proxies, api_keys, infuras)]

                        #list = await get_effective_transactions(address, clients[0])

                        #print(f"\n\neffective txs: {list}\n\n") 

                        oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop = await asynciohopanalysis.analyze_address_hops(deployer_address, clients, hop=1, max_hops=5, max_txs=100,tx_path = None, tx_count_per_hop=None)




                        #first print of random data
                    print(f"\nOldest connected wallet: {oldest_wallet_per_hop}")
                    print(f"\nRichest connected wallet: {richest_wallet_per_hop}")
                    if winning_data_per_hop:
                        print(f"\nWinning data: {winning_data_per_hop}")
                    print(f"\ntransaction count per hop {tx_count_per_hop}")
                    print(f"\nliq removal data {liq_removal_data_per_hop}\n")
                    print(f"\n total liq removals {total_liq_removals}")

                        # Remove 'None' elements
                    oldest_wallet_per_hop = [i for i in oldest_wallet_per_hop if i]
                    richest_wallet_per_hop = [i for i in richest_wallet_per_hop if i]
                    winning_data_per_hop = [i for i in winning_data_per_hop if i]
                    liq_removal_data_per_hop = [i for i in liq_removal_data_per_hop if i]

                    # Filter oldest_wallet_per_hop
                    oldest_wallet_per_hop = [i for i in oldest_wallet_per_hop if i['age'] > 365]
                    #oldest_age = max(item['age'] for item in oldest_wallet_per_hop if item)
                    if any(item for item in oldest_wallet_per_hop):
                        oldest_age = max(item['age'] for item in oldest_wallet_per_hop if item)
                    else:
                        oldest_age = None

                    for i, item in enumerate(oldest_wallet_per_hop):
                        if item and item['age'] == oldest_age:
                            oldest_wallet_per_hop =  oldest_wallet_per_hop[:i+1]


                    # Filter richest_wallet_per_hop
                    richest_wallet_per_hop = [i for i in richest_wallet_per_hop if i['balance'] > 5]
                    # richest_balance = max(item['balance'] for item in richest_wallet_per_hop if item)
                    if any(item for item in richest_wallet_per_hop):
                        richest_balance = max(item['balance'] for item in richest_wallet_per_hop if item)
                    else:
                        richest_balance = None

                    for i, item in enumerate(richest_wallet_per_hop):
                        if item and item['balance'] == richest_balance:
                            richest_wallet_per_hop =  richest_wallet_per_hop[:i+1]

                    # Filter winning_data_per_hop
                    winning_data_per_hop.sort(key=lambda x: x['hop'])
                    # Then, remove duplicates, keeping only the first occurrence (which has the lowest 'hop' thanks to the sort)
                    seen = set()
                    winning_data_per_hop = [i for i in winning_data_per_hop if not (i['address'] in seen or seen.add(i['address']))]

                    #all the nice text
                    raw_summary = f"Oldest connected wallet: {oldest_wallet_per_hop}\n\n Richest connected wallet: {richest_wallet_per_hop} \n\n"
                    if winning_data_per_hop:
                        raw_summary += f"\n\n Winning data: {winning_data_per_hop}"
                    raw_summary += f"\ntransaction count per hop {tx_count_per_hop}\n\nliq removal data {liq_removal_data_per_hop}\ntotal liq removals {total_liq_removals}"
                    print(f"{raw_summary}")



                    # Using the given example data to generate the summary text
                    main_text, details_text = asynciohopanalysis.generate_summary_text(oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop)
                    #we add the data to the token  
                    hop_message = main_text + f"{details_text}"
                    print(f"\n\nsummary: {hop_message}\n\n")
                    
                    # Define the filter and the update
                    filter_ = {"_id": f"{contract_address}"}
                    update_ = {
                        "$set": {
                            "hop_message": f"{hop_message}",
                            "hop_analysis": {
                                "hop_message": f"{hop_message}",
                                "oldest_data" : oldest_wallet_per_hop,
                                "richest_data": richest_wallet_per_hop,
                                "winning_data": winning_data_per_hop,
                                "liquidity_data": liq_removal_data_per_hop
                            }
                        }
                    }

                    # Use upsert=True to insert if not exists, or update if exists
                    tokens.update_one(filter_, update_, upsert=False)


                    # Fetch token data by contract address
                    token_data = database_manager.get_token_data(contract_address)
                    print(f"\n\nThis is the mongo db token data {token_data}")
                    
                    # Check if the token data was found
                    if token_data is not None:
                        
                        # Extract event data from the token data document
                        deployed_event = token_data.get("events", {}).get("deployed", {})
                        verified_event = token_data.get("events", {}).get("verified", {})
                        locked_event = token_data.get("events", {}).get("locked", {})
                        burned_event = token_data.get("events", {}).get("burned", {})
                        
                        # Extract message_id and message_text from each event data
                        deployed_message_id = deployed_event.get("message_id", None)
                        deployed_message = deployed_event.get("message_text", None)
                        verified_message_id = verified_event.get("message_id", None)
                        verified_message = verified_event.get("message_text", None)
                        lock_message_id = locked_event.get("message_id", None)
                        lock_message = locked_event.get("message_text", None)
                        burn_message_id = burned_event.get("message_id", None)
                        burn_message = burned_event.get("message_text", None)
                        
                        #After finishing the analysis we edit the already posted messages with the contract address as a key
                        if deployed_message_id is not None:
                            if hop_message != "":
                                # Edit the message in the target channel with new content
                                new_text = deployed_message + hop_message
                                await clientTG.edit_message(target_deployed, deployed_message_id, new_text, parse_mode='md')

                        if verified_message_id is not None:
                            if hop_message != "":
                                # Edit the message in the target channel with new content
                                new_text = verified_message + hop_message
                                await clientTG.edit_message(target_verified, verified_message_id, new_text, parse_mode='md')

                        if lock_message_id is not None:
                            if hop_message != "":
                                # Edit the message in the target channel with new content
                                new_text = lock_message + hop_message
                                await clientTG.edit_message(target_longlock, lock_message_id, new_text, parse_mode='md')

                        if burn_message_id is not None:
                            if hop_message != "":
                                # Edit the message in the target channel with new content
                                new_text = burn_message + hop_message
                                await clientTG.edit_message(target_burn, burn_message_id, new_text, parse_mode='md')

                    print(f"\n telegram deployed forwarder finished in: {round(time.time() - start, 2)} seconds \n")

                    logger.info("Forwarded message to target channel")

        logger.info("Bot is running...")
        await clientTG.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
