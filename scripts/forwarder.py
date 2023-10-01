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
    match = re.search(r"\[Deployer\]\(https://etherscan.io/address/(.*?)\)", text)
    if match:
        return match.group(1)
    else:
        return None


def treatment_message_text(message_text, tokens):
    contract_address = caextractor.extract_contract_address(message_text)

    if contract_address:
        
        logger.info(
            f"Extracted contract address: {contract_address}")
        
        token_data = tokens.find_one({"_id": contract_address})
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
            telegram_links, twitter_links, discord_links, other_websites, medium_links, triple_links, social_media_text = None, None, None, None, None, None, None

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
                        telegram_links, twitter_links, discord_links, other_websites, medium_links, triple_links, social_media_text = result
                    elif future == task5_future:
                        number_lpremove, tx_lpremove = result

                except Exception as e:
                    print(f"Exception occurred during task execution: {e}")


                        
        if int(pastcoins[3]) > 0:
            addy = pastcoins[0]
            past_name, past_symbol = ethsourcecode.get_name_symbol(addy)
            contracts_deployed_count = pastcoins[2]

        

          # Remove everything below the _ character in the message text
        if "___" in message_text:
            message_text = re.sub(r"___.*", "", message_text, flags=re.DOTALL)
        else:
            message_text = re.sub(r"☎️.*", "", message_text, flags=re.DOTALL)

        # Define the regular expression pattern for the specified format
        pattern = r"🔗 (\[TG\]\(.*?\)? 🤷‍♂️|\[TG\]\(.*?\)?|TG 🤷‍♂️)? \| (Web 🤷‍♂️|\[Web\]\(.*?\)? 🤷‍♂️|\[Web\]\(.*?\)?|Web)? \| (Twitter 🤷‍♂️|\[Twitter\]\(.*?\)? 🤷‍♂️|\[Twitter\]\(.*?\)?|Twitter)? \|"       
        # Use the re.sub() function to remove all matches of the pattern from the text
        message_text = re.sub(pattern, "", message_text, flags=re.IGNORECASE)
        ##############################################################
        
        message_text += f"\n\n---------------------------------\n** ⟹💲 Marketcap:**  `{mcap}`\n** ⟹💧 Liquidity:**  `{liquidity}`\n"

        if social_media_text.strip(): 
            message_text += f"\n---------------------------------\n 🌐 **SOCAL LINKS** 🌐  \n ⯆\n{social_media_text}"
        ##############################################################

        message_text +=f"\n---------------------------------\n**📈DEPLOYER DETAILS:**\n ⯆\n"
        if deployer_name is not None:
            message_text += f"**  ⟹⚡️ Nametag:**  `{deployer_name}`\n"
        
        if len(cexfunded)>0 :
            message_text += f"**  ⟹🔹 Cex:** `{cexfunded}`\n"

        if balance_eth is not None:
            message_text += f"**  ⟹💰 Balance:**  `{round_balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"
        else:
            message_text += f"**  ⟹💰 Balance:**  `{balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"
        
        if number_lpremove is not None:
            if number_lpremove > 0 :
                message_text += f"**  ⟹🛑 liq remove Txs** : `{number_lpremove}` \n     **⟹** `{tx_lpremove}` \n"

        if int(pastcoins[1]) != 0:
            message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN**`(out of {contracts_deployed_count})`\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n **  ⟹🎯 ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
        elif int(pastcoins[2]) > 0: #checks if no ath mcap data is available but there is a high tx past coin
                        message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n "

        return message_text, contract_address



#Main
async def main():
    async with TelegramClient("ubuntusession", api_id, api_hash) as client:
        @client.on(events.NewMessage(chats=source_channel))
        async def my_event_handler(event):
            start = time.time()
            message = event.message
            message_text = message.text
            logger.info(f"message text: {message_text}")

            #freshly deployed tokens #####################################################################################
            if "Deployed" in message_text and "🛑" not in message_text:
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
                    #mcap, liquidity = ethsourcecode.get_marketcap(contract_address)
                    cexfunded = ethsourcecode.extract_nametags_and_addresses(deployer_address, proxy)
                    number_lpremove, txs_lpremove = ethsourcecode.detect_liquidity_removals(deployer_address, f"{ETHERSCAN_API_KEY3}", None, None)
                    
                    #get the pastcoins if there is anything interesting
                    pastcoins = ethsourcecode.fpc(contract_address, f"{ETHERSCAN_API_KEY}", None, None)
                    
                    if int(pastcoins[3]) > 0:
                        addy = pastcoins[0]
                        past_name, past_symbol = ethsourcecode.get_name_symbol(addy)
                        contracts_deployed_count = pastcoins[2]

                    # get the social media urls organised from the source code
                    telegram_links, twitter_links, discord_links, other_websites, medium_links, triple_links, social_media_text = ethsourcecode.get_socialmedia_filter(contract_address, f"{ETHERSCAN_API_KEY2}", None, None)
                    

                   
                    
                      # Remove everything below the _ character in the message text
                    if "___" in message_text:
                        message_text = re.sub(r"___.*", "", message_text, flags=re.DOTALL)
                    else:
                        message_text = re.sub(r"☎️.*", "", message_text, flags=re.DOTALL)

                    # Define the regular expression pattern for the specified format
                    pattern = r"🔗 (\[TG\]\(.*?\)? 🤷‍♂️|\[TG\]\(.*?\)?|TG 🤷‍♂️)? \| (Web 🤷‍♂️|\[Web\]\(.*?\)? 🤷‍♂️|\[Web\]\(.*?\)?|Web)? \| (Twitter 🤷‍♂️|\[Twitter\]\(.*?\)? 🤷‍♂️|\[Twitter\]\(.*?\)?|Twitter)? \|"
                    
                    # Use the re.sub() function to remove all matches of the pattern from the text
                    message_text = re.sub(pattern, "", message_text, flags=re.IGNORECASE)

                    
                    ##############################################################
                    
                    #message_text += f"---------------------------------\n** ⟹💲 Marketcap:**  `{mcap}`\n** ⟹💰 Liquidity:**  `{liquidity}`\n"

                    if social_media_text.strip(): 
                        message_text += f"\n---------------------------------\n 🌐 **SOCAL LINKS** 🌐  \n ⯆\n{social_media_text}"
                    ##############################################################

                    message_text +=f"\n---------------------------------\n**📈DEPLOYER DETAILS:**\n ⯆\n"
                    if deployer_name is not None:
                        message_text += f"**  ⟹⚡️ Nametag:**  `{deployer_name}`\n"
                    
                    if len(cexfunded)>0 :
                        message_text += f"**  ⟹🔹 Cex:** `{cexfunded}`\n"
                    if balance_eth is not None:
                        message_text += f"**  ⟹💰 Balance:**  `{round_balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"
                    else:
                        message_text += f"**  ⟹💰 Balance:**  `{balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"


                    if number_lpremove is not None:
                        if number_lpremove > 0 :
                            message_text += f"**  ⟹🛑 liq remove Txs** : `{number_lpremove}` \n     **⟹** `{tx_lpremove}` \n"
                    
                    if pastcoins[1] != 0: #checks if one ath Mcap past ca at least exists
                        message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN `(out of {contracts_deployed_count})`**\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n **  ⟹🎯 ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
                    elif int(pastcoins[2]) > 0: #checks if no ath mcap data is available but there is a high tx past coin
                        message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n "
                    
                    # Send the message and capture the returned Message object
                    sent_message = await client.send_message(target_deployed, message_text, parse_mode='md', link_preview=False)

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id
                    timestamp_utc = sent_message.date
                    print(f"\n telegram deployed forwarder finished in: {round(time.time() - start, 2)} seconds \n")
                    
                    
                    #Mongo db add document with data

                    # Sample data
                    filter_ = {"_id": contract_address}
                    update_ = {
                        "$setOnInsert": {
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
            if "Verified" in message_text and "🛑" not in message_text:
                logger.info("Found a verified contract message")         

                contract_address = caextractor.extract_contract_address(message_text)
                hopanalysis = None
                
                if contract_address:
                    
                    logger.info(
                        f"Extracted contract address: {contract_address}")
                    ###########################################

                    # Fetch the document
                    token_data = tokens.find_one({"_id": contract_address})
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
                        telegram_links, twitter_links, discord_links, other_websites, medium_links, triple_links, social_media_text = None, None, None, None, None, None, None
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
                                    telegram_links, twitter_links, discord_links, other_websites, medium_links, triple_links, social_media_text = result
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
                    

                    # Remove everything below the _ character in the message text
                    if "___" in message_text:
                        message_text = re.sub(r"___.*", "", message_text, flags=re.DOTALL)
                    else:
                        message_text = re.sub(r"☎️.*", "", message_text, flags=re.DOTALL)

                    # Define the regular expression pattern for the specified format
                    pattern = r"🔗 (\[TG\]\(.*?\)? 🤷‍♂️|\[TG\]\(.*?\)?|TG 🤷‍♂️)? \| (Web 🤷‍♂️|\[Web\]\(.*?\)? 🤷‍♂️|\[Web\]\(.*?\)?|Web)? \| (Twitter 🤷‍♂️|\[Twitter\]\(.*?\)? 🤷‍♂️|\[Twitter\]\(.*?\)?|Twitter)? \|"
                    
                    # Use the re.sub() function to remove all matches of the pattern from the text
                    message_text = re.sub(pattern, "", message_text, flags=re.IGNORECASE)


                    
                    ##############################################################
                    
                    message_text += f"\n---------------------------------\n** ⟹💲 Marketcap:**  `{mcap}`\n** ⟹💧 Liquidity:**  `{liquidity}`\n"

                    if social_media_text.strip(): 
                        message_text += f"\n---------------------------------\n 🌐 **SOCAL LINKS** 🌐  \n ⯆\n{social_media_text}"
                    ##############################################################

                    message_text +=f"\n---------------------------------\n**📈DEPLOYER DETAILS:**\n ⯆\n"
                    if deployer_name is not None:
                        message_text += f"**  ⟹⚡️ Nametag:**  `{deployer_name}`\n"
                    
                    if len(cexfunded)>0 :
                        message_text += f"**  ⟹🔹 Cex:** `{cexfunded}`\n"

                    if balance_eth is not None:
                        message_text += f"**  ⟹💰 Balance:**  `{round_balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"
                    else:
                        message_text += f"**  ⟹💰 Balance:**  `{balance_eth}` **ETH**\n**  ⟹🕰 Age:**  `{deployer_age}` **days**\n"

                    if number_lpremove is not None and number_lpremove>0 :
                        message_text += f"**  ⟹🛑 liq remove Txs** : `{number_lpremove}` \n     **⯆** `{tx_lpremove}` \n"
                    
                    if pastcoins[1] != 0:
                        message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n **  ⟹🎯 ATH mcap:** `{ethsourcecode.smart_format_number(pastcoins[1])}`"
                    elif int(pastcoins[2]) > 0:
                        message_text += f"\n---------------------------------\n **🤖 BEST PAST COIN** `(out of {contracts_deployed_count})`\n ⯆\n **  ⟹ Name:** `{past_name}` \n **  ⟹ Symbol:** `{past_symbol}` \n **  ⟹ Ca:** `{pastcoins[0]}` \n "

                    if hopanalysis is not None:
                        if hopanalysis != "":
                            message_text += f"{hopanalysis}"

                    

                    sent_message = await client.send_message(target_verified, message_text, parse_mode='md', link_preview=False)
                    print(f"\n telegram verified forwarder finished in: {round(time.time() - start, 2)} seconds \n")

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id
                    timestamp_utc = sent_message.date

                    # Define the filter and the update
                    filter_ = {"_id": contract_address}
                    update_ = {
                        "$set": {
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
                                "triple": triple_links
                            }

                        }
                    }

                    # Use upsert=True to insert if not exists, or update if exists
                    tokens.update_one(filter_, update_, upsert=True)




                    logger.info("Forwarded message to target channel")
            
            
            ###############################################################################################
            #Burned Tokens ################################################################################
            if "burned" in message_text and "🛑" not in message_text:
                logger.info("Found a verified contract message")
                
                message_text, contract_address = treatment_message_text(message_text, tokens)    

                sent_message = await client.send_message(target_burn, message_text, parse_mode='md', link_preview=False)

                # Now, you can access the message ID using sent_message.id
                message_id = sent_message.id

                timestamp_utc = sent_message.date

                # Define the filter and the update
                filter_ = {"_id": contract_address}
                update_ = {
                    "$set": {
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
                if days > 180 and "🛑" not in message_text:
                    logger.info("Found a Long Lock contract message")
                
                    message_text, contract_address = treatment_message_text(message_text, tokens)

                    sent_message = await client.send_message(target_longlock, message_text, parse_mode='md', link_preview=False)

                    # Now, you can access the message ID using sent_message.id
                    message_id = sent_message.id

                    timestamp_utc = sent_message.date

                    # Define the filter and the update
                    filter_ = {"_id": contract_address}
                    update_ = {
                        "$set": {
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
