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
from modules import asyncioethsourcecode
import asyncio
from aiolimiter import AsyncLimiter
import web3
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from itertools import cycle


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



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)







async def make_api_calls(transactions, clients):
    results = []
    tasks = []

    # Extracting the addresses for balance check
    from_addresses = [tx[1] for tx in transactions]
    #Making the bulk balance api call on etherscan
    balance_lookup = {}
    balance_endpoint = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={','.join(from_addresses)}&tag=latest&apikey={clients[0].api_key}"
    balance_response = await clients[0].get(balance_endpoint)
    balance_data = balance_response.json()
    if balance_data.get("status") == "1":
        for item in balance_data["result"]:
            w3 = Web3()
            balance_eth = w3.from_wei(int(item["balance"]), "ether")
            balance_lookup[item["account"]] = balance_eth

    # Add the balances to the all_transactions list
    for idx, tx in enumerate(transactions):
        tx_list = list(tx)
        tx_balance =balance_lookup.get(tx[1], '0')
        tx_list.append(tx_balance)
        transactions[idx] = tx_list




    for i, transaction in enumerate(transactions):
        tasks.append(filter_tx_tuples(transaction, clients[i]))

    for future in asyncio.as_completed(tasks):
        try:
            result = await future
            print(f"here I print result to debug {result}")  # debug line
            results.append(result)
        except Exception as e:
            print(f"make api calls function | API request error: {e}")

    return results




async def filter_tx_tuples(transaction, client):
    result = []

    #limiter = AsyncLimiter(9, 1.2)  # This will allow 5 calls per 1 second, adjust as needed.


    # mcap_data = await asyncioethsourcecode.filter_pastcoin_contracts(transaction[1], client)
    # age = await asyncioethsourcecode.get_age(transaction[1], client)
    # balance = await asyncioethsourcecode.get_balance(transaction[1], client)
    #async with limiter:  # This will ensure rate limitin
    mcap_data_age =  await asyncioethsourcecode.filter_pastcoin_contracts_and_age(transaction[1], client)

    balance = transaction[3]
    mcap_data1, mcap_data2, age = mcap_data_age
    mcap_data =mcap_data1, mcap_data2

    result.append(transaction)
    result.append(mcap_data)
    result.append(age)
    result.append(balance)

    return result














#checks if an address is a contract INFURA
async def is_contract_address(address):
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))

    checksum_address = web3.Web3.to_checksum_ddress(address)
    code = await w3.eth.getCode(checksum_address)
    return len(code) > 2

async def get_transaction_count(address, client):
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{client.infuras}'))
    checksum_address = web3.Web3.to_checksum_address(address)
    transaction_count = w3.eth.get_transaction_count(checksum_address)
    return transaction_count




async def get_effective_transactions(address, clients):
    
    for i in range(0,11):
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={clients[i].api_key}"

        try:
            response = await clients[i].get(url)
            data = response.json()
            if data["status"] == "1":
                transactions = data["result"]

                tx_count = len(transactions)

                address_set = set()  # Set to store unique addresses
                address_set.add('')
                all_transactions = []
                liq_removal_txs = []  # List to store liquidity removal transactions

                for tx in transactions:
                    from_address = tx["from"].lower()
                    to_address = tx["to"].lower()
                    value_eth = Decimal(tx["value"]) / 10**18  # Convert wei to ETH
                    # Check if the transaction is a liquidity removal
                    if "remove" in tx["functionName"].lower() and "liquidity" in tx["functionName"].lower():
                        liq_removal_txs.append(tx["hash"])
                    # get the in addresses
                    if to_address == address.lower() and from_address != address.lower() and value_eth > 0:
                        if from_address not in address_set and await get_transaction_count(from_address, clients[i]) < 4000:
                            address_set.add(from_address)
                            all_transactions.append((tx["hash"], from_address, "in"))
                            if len(all_transactions) >= 100:  #we analyse max 100 transactions now, change if needed
                                break


                transaction_count = len(all_transactions)
                liq_removal_count = len(liq_removal_txs)

                return all_transactions, transaction_count, liq_removal_txs
        except httpx.RequestError as e:
            print(f"Etherscan txlist Error: {e}")

    return None, -1, []



async def get_effective_transactionsv2(address, client):
    shitlist = ["0xC4B1b1EC2dA9868f6Fbc5274Fc0983788DB4230A", "0x7A01b95C2E232d250db9E106DCF317E29A1279ab"]
    start = time.time()
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={client.api_key}"

    try:
        response = await client.get(url)
        data = response.json()
        if data["status"] == "1":
            transactions = data["result"]

            tx_count = len(transactions)

            address_set = set()  # Set to store unique addresses
            address_set.add('')
            all_transactions = []
            liq_removal_txs = []  # List to store liquidity removal transactions

            for tx in transactions:
                from_address = tx["from"].lower()
                to_address = tx["to"].lower()
                value_eth = Decimal(tx["value"]) / 10**18  # Convert wei to ETH
                
                # Check if the transaction is a liquidity removal
                if "remove" in tx["functionName"].lower() and "liquidity" in tx["functionName"].lower():
                    liq_removal_txs.append(tx["hash"])
                
                # Get the incoming addresses and limit to first 100
                if to_address == address.lower() and from_address != address.lower():
                    if from_address not in address_set and await get_transaction_count(from_address, client) < 8000 and value_eth > 0.001:
                        address_set.add(from_address)
                        all_transactions.append([tx["hash"], from_address, "in"])
                        # if len(all_transactions) >= 100:   #since we analyze at most 100 txs total change if needed
                        #     break

            # Extracting the addresses for balance check
            from_addresses = [tx[1] for tx in all_transactions]

            # Chunk the addresses into groups of 20
            address_chunks = [from_addresses[i:i+20] for i in range(0, len(from_addresses), 20)]

            balance_lookup = {}
            for chunk in address_chunks:
                balance_endpoint = f"https://api.etherscan.io/api?module=account&action=balancemulti&address={','.join(chunk)}&tag=latest&apikey={client.api_key}"
                balance_response = await client.get(balance_endpoint)
                balance_data = balance_response.json()
                if balance_data.get("status") == "1":
                    for item in balance_data["result"]:
                        w3 = Web3()
                        balance_eth = w3.from_wei(int(item["balance"]), "ether")
                        balance_lookup[item["account"]] = balance_eth

            # Add the balances to the all_transactions list
            for tx in all_transactions:
                tx.append(balance_lookup.get(tx[1], '0'))

            transaction_count = len(all_transactions)
            liq_removal_count = len(liq_removal_txs)
            print(f"get effective txs took {round(time.time()-start,2)}")
            return all_transactions, transaction_count, liq_removal_txs
    except httpx.RequestError as e:
        print(f"Etherscan txlist Error: {e}")

    return None, -1, []



# (Analyze_address and analyze_address_hops functions go here...)









async def analyze_address(address, hop, max_hops, tx_path, tx_count_per_hop, clients):
    client = random.choice(clients)
    txList, tx_count, liq_removal_txs = await get_effective_transactions(address, clients)  # Receive liq_removal_txs

    
    tx_count_per_hop[hop-1] += tx_count  # Update the count
    oldest_wallet = None
    richest_wallet = None
    winning_data = None
    next_hop_addresses = []
    liq_removal_wallet = None  # Initialize liq_removal_wallet

    if tx_count > 0:
        tupleList_chunks = [txList[i:i+10] for i in range(0, len(txList), 7)]
        
        for i, item in enumerate(tupleList_chunks):
            results = await make_api_calls(item, clients)  # Shift the client index by i*5 for each chunk

            for result in results:
                new_tx_path = tx_path + [result[0][0]]
                if oldest_wallet is None or result[2] > oldest_wallet['age']:
                    oldest_wallet = {'tx_path': new_tx_path, 'hop': hop, 'address': result[0][1], 'age': result[2]}
                if richest_wallet is None or result[3] > richest_wallet['balance']:
                    richest_wallet = {'tx_path': new_tx_path, 'hop': hop, 'address': result[0][1], 'balance': result[3]}
                if result[1][1] is not None and (winning_data is None or result[1][1] > winning_data['max_mcap']):
                    winning_data = {'tx_path': new_tx_path, 'hop': hop, 'address': result[1][0], 'max_mcap': result[1][1]}
                next_hop_addresses.append((result[0][1], new_tx_path))  # Add the updated tx_path here
                if liq_removal_txs:
                    liq_removal_wallet = {'tx_path': tx_path, 'hop': hop-1, 'address': address, 'liquidity_removals': len(liq_removal_txs), 'liq_removal_txs': liq_removal_txs}

    return oldest_wallet, richest_wallet, winning_data, liq_removal_wallet, next_hop_addresses  # Return liq_removal_wallet


async def analyze_address_hops(address, clients, hop=1, max_hops=5, max_txs=3, tx_path=None, tx_count_per_hop=None):
    
    if tx_path is None:
        tx_path = []

    if tx_count_per_hop is None:
        tx_count_per_hop = [0] * max_hops  # Initialize only once

    processed_addresses = set()

    oldest_wallet_per_hop = [None] * max_hops
    richest_wallet_per_hop = [None] * max_hops
    winning_data_per_hop = [None] * max_hops

    hop_execution_time = [0] * max_hops

    addresses_to_analyze = [(address, tx_path)]  # Start with the initial address and tx_path

    liq_removal_data_per_hop = [None] * max_hops  # Initialize liq_removal_data_per_hop
    total_liq_removals = 0  # Initialize total count of liquidity removals

    continue_processing = True  # Initialize flag

    for current_hop in range(hop, max_hops+1):
        start = time.time()
        next_hop_addresses = []

        if not continue_processing:  # Check the flag at the start of each hop
            break

        for addr, tx_path in addresses_to_analyze:  # Unpack both the address and tx_path here
            if addr in processed_addresses:
                continue

            if sum(tx_count_per_hop) < max_txs:
                oldest_wallet, richest_wallet, winning_data, liq_removal_wallet, addr_next_hop_addresses = await analyze_address(addr, current_hop, max_hops, tx_path, tx_count_per_hop, clients)  # Receive liq_removal_wallet
                processed_addresses.add(addr)
                next_hop_addresses.extend(addr_next_hop_addresses)

                if oldest_wallet is not None and (oldest_wallet_per_hop[current_hop-1] is None or oldest_wallet['age'] > oldest_wallet_per_hop[current_hop-1]['age']):
                    oldest_wallet_per_hop[current_hop-1] = oldest_wallet

               #if richest_wallet is not None and (richest_wallet_per_hop[current_hop-1] is None or richest_wallet['balance'] > richest_wallet_per_hop[current_hop-1]['balance']):
                   #richest_wallet_per_hop[current_hop-1] = richest_wallet
                if richest_wallet is not None:
                    richest_wallet['balance'] = round(float(richest_wallet['balance']), 3)
                    if (richest_wallet_per_hop[current_hop-1] is None or richest_wallet['balance'] > richest_wallet_per_hop[current_hop-1]['balance']):
                        richest_wallet_per_hop[current_hop-1] = richest_wallet


                if winning_data is not None and (winning_data_per_hop[current_hop-1] is None or winning_data['max_mcap'] > winning_data_per_hop[current_hop-1]['max_mcap']):
                    winning_data_per_hop[current_hop-1] = winning_data

                if liq_removal_wallet is not None:
                    total_liq_removals += liq_removal_wallet['liquidity_removals']  # Update the total count
                    if liq_removal_data_per_hop[current_hop-1] is None or liq_removal_wallet['liquidity_removals'] > liq_removal_data_per_hop[current_hop-1]['liquidity_removals']:
                        liq_removal_data_per_hop[current_hop-1] = liq_removal_wallet

            else:
                continue_processing = False  # Set the flag to False
                break  # Break the inner loop
        hop_execution_time[current_hop-1] = round(time.time()- start, 2)
        addresses_to_analyze = next_hop_addresses

    print(f"\n\n Execution time per hop: {hop_execution_time}")

    return oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop  # Return total_liq_removals



class CustomClient(httpx.AsyncClient):
    def __init__(self, *args, api_key, proxies=None, headers=None, infuras=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.proxies = proxies
        self.headers = headers
        self.infuras = infuras



def shorten_and_link(eth_strings):
    if not isinstance(eth_strings, list):
        eth_strings = [eth_strings]
    
    result = []
    
    for eth_string in eth_strings:
        if not eth_string.startswith('0x') or len(eth_string) not in (42, 66):
            raise ValueError("Invalid Ethereum address or transaction hash")
        
        short_version = f'0x..{eth_string[-2:]}'
        
        if len(eth_string) == 42:
            url = f'https://etherscan.io/address/{eth_string}'
        else:
            url = f'https://etherscan.io/tx/{eth_string}'
            
        result.append(f'[{short_version}]({url})')
    
    return result

#function to generate good summary text for when posting on telegram
def generate_summary_text(oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop,    total_liq_removals, tx_count_per_hop):
        main_text = ""
        details_text = ""

        # Main Text
        # Highest market cap from winning data
        if winning_data_per_hop:
            max_mcap_wallet = max(winning_data_per_hop, key=lambda x: x['max_mcap'])
            for tx in max_mcap_wallet['tx_path']:
                tx = shorten_and_link(tx)
            main_text += f"\n at hop {max_mcap_wallet['hop']} from `{asyncioethsourcecode.get_name_symbol(max_mcap_wallet['address'])}` , **ATH MC:** `{asyncioethsourcecode.smart_format_number(max_mcap_wallet['max_mcap'])}`,  ca: `{max_mcap_wallet['address']}`. Transaction path: {', '.join(shorten_and_link(max_mcap_wallet['tx_path']))}\n"

        # Oldest wallet available
        if oldest_wallet_per_hop:
            oldest_wallet = max(oldest_wallet_per_hop, key=lambda x: x['age'])
            main_text += f"** ⟹**The oldest connected wallet is `{oldest_wallet['age']}` **days** old at hop `{oldest_wallet['hop']}`, address: {shorten_and_link(oldest_wallet['address'])} .\n"

        # Richest wallet available
        if richest_wallet_per_hop:
            richest_wallet = max(richest_wallet_per_hop, key=lambda x: x['balance'])
            main_text += f"** ⟹**The richest connected wallet has {round(richest_wallet['balance'],2)} ETH, is at hop {richest_wallet['hop']}, address: {shorten_and_link(richest_wallet['address'])} \n"
        
        # Total liq removals number
        if total_liq_removals > 0:
            main_text += f"** ⟹**🛑 Total liquidity removals: {total_liq_removals}\n"

        if total_liq_removals > 0 or richest_wallet_per_hop or oldest_wallet_per_hop or winning_data_per_hop:
            main_text = f"\n---------------------------------\n**📈HOP ANALYSIS:**\n ⯆\n" + main_text

        ########## Details Text
        max_hops = len(tx_count_per_hop)
        for hop in range(1, max_hops + 1):
            current_hop_details = []
            
            # Highest mcap for current hop
            hop_winning_data = [data for data in winning_data_per_hop if data['hop'] == hop]
            if hop_winning_data:
                max_mcap_wallet_hop = max(hop_winning_data, key=lambda x: x['max_mcap'])
                current_hop_details.append(f"** ⟹**{asyncioethsourcecode.get_name_symbol(max_mcap_wallet_hop['address'])}, ATH MC: {asyncioethsourcecode.smart_format_number(max_mcap_wallet_hop['max_mcap'])}, CA: {shorten_and_link(max_mcap_wallet_hop['address'])}.")

            # Oldest address for current hop
            hop_oldest_wallet = [data for data in oldest_wallet_per_hop if data['hop'] == hop]
            if hop_oldest_wallet:
                oldest_wallet_hop = max(hop_oldest_wallet, key=lambda x: x['age'])
                current_hop_details.append(f"** ⟹**Oldest address is {shorten_and_link(oldest_wallet_hop['address'])} with age `{oldest_wallet_hop['age']}` **days**.")

            # Richest wallet for current hop
            hop_richest_wallet = [data for data in richest_wallet_per_hop if data['hop'] == hop]
            if hop_richest_wallet:
                richest_wallet_hop = max(hop_richest_wallet, key=lambda x: x['balance'])
                current_hop_details.append(f"** ⟹**Richest wallet is {shorten_and_link(richest_wallet_hop['address'])} with a balance `{round(richest_wallet_hop['balance'],2)}` **ETH**.")

            # Number of liquidity removals for current hop
            hop_liq_removal_data = [data for data in liq_removal_data_per_hop if data['hop'] == hop]
            if hop_liq_removal_data:
                total_removals_hop = sum(item['liquidity_removals'] for item in hop_liq_removal_data)
                if total_removals_hop > 0:
                    current_hop_details.append(f"** ⟹**Liquidity removals: `{total_removals_hop}`.")

            # Only add the hop details if there's relevant data
            if current_hop_details:
                details_text += f"\n** hop {hop}:**\n"
                details_text += "\n".join(current_hop_details)

        return main_text, details_text




#Main function for this file, it gets executed only if you run this file directly

async def main():
    address = input("Enter an ethereum contract address: ")
    start = time.time()
    async with httpx.AsyncClient() as client:
        api_key = f"{ETHERSCAN_API_KEY6}"
          # Define your API keys, proxies, and headers
        api_keys = [f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY5}", f"{ETHERSCAN_API_KEY6}", f"{ETHERSCAN_API_KEY7}",f"{ETHERSCAN_API_KEY8}",f"{ETHERSCAN_API_KEY9}",f"{ETHERSCAN_API_KEY12}", f"{ETHERSCAN_API_KEY10}",f"{ETHERSCAN_API_KEY11}"]
        
        #proxies setup in clients
        proxies = [f"{PROXY1}", f"{PROXY2}", f"{PROXY3}", f"{PROXY4}", f"{PROXY5}", f"{PROXY6}", f"{PROXY7}", f"{PROXY8}", f"{PROXY9}", f"{PROXY10}", None]
        
        #headers setup in clients
        headers = [f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT5}", f"{USER_AGENT6}",f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}",f"{USER_AGENT2}", f"{USER_AGENT3}"]
        
        #infura api key
        infuras = [f"{INFURA_API_KEY}", f"{INFURA_API_KEY4}",f"{INFURA_API_KEY7}",f"{INFURA_API_KEY2}", f"{INFURA_API_KEY5}",f"{INFURA_API_KEY8}",f"{INFURA_API_KEY3}", f"{INFURA_API_KEY6}",f"{INFURA_API_KEY9}",f"{INFURA_API_KEY3}", f"{INFURA_API_KEY6}",f"{INFURA_API_KEY9}"]


        # Create a list of dictionaries, where each dictionary represents a client
        clients = [CustomClient(headers={"User-Agent": user_agent}, proxies={"http://": proxy, "https://": proxy}, api_key=api_key, infuras=infuras) for user_agent, proxy, api_key, infuras in zip(headers, proxies, api_keys, infuras)]

        #list = await get_effective_transactions(address, clients[0])

        #print(f"\n\neffective txs: {list}\n\n") 

        oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop = await analyze_address_hops(address, clients, hop=1, max_hops=9, max_txs=200,tx_path = None, tx_count_per_hop=None)




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
    main_text, details_text = generate_summary_text(oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop)

    print(f"\n\n\n{main_text}\n {details_text}")
    print(f"finished after {round(time.time() - start, 2)} seconds")
if __name__ == "__main__":
    asyncio.run(main())

 
