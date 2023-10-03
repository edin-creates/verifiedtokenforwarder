import requests
import httpx
import logging
import re
import concurrent.futures
import time
import random
from decimal import Decimal
from web3 import Web3
import os
from dotenv import load_dotenv
from datetime import datetime
import ethsourcecode
import asyncioethsourcecode
import asyncio


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



INFURA_API_KEY = os.environ['INFURA_API_KEY']
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)






#Function that returns the top mcap added to a tuple {txid, address, inorout}
def filter_tx_tuplesv2(transaction, api_key, proxy, header):
    result = []
    tx_id, address, inorout = transaction
    mcapdata = ethsourcecode.filter_pastcoin_contracts(address, api_key, proxy, header)
    print(f"mcapdata: {mcapdata}, type: {type(mcapdata)}")
    
    balance = ethsourcecode.get_balance(address, api_key, proxy, header)
    print(f"balance: {balance}, type: {type(balance)}")
    
    age = ethsourcecode.get_age(address, api_key, proxy, header)
    print(f"age: {age}, type: {type(age)}")
    
    result.append(transaction)
    result.append(mcapdata)
    result.append(age)
    result.append(balance)

    return result

def filter_tx_tuples(transaction, api_key, proxy, header):
    start = time.time()
    # result = []
    tx_id, address, inorout = transaction

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_mcapdata = executor.submit(ethsourcecode.filter_pastcoin_contracts, address, api_key, proxy, header)
        future_age = executor.submit(ethsourcecode.get_age, address, api_key, proxy, header)
        future_balance = executor.submit(ethsourcecode.get_balance, address, api_key, proxy, header)

    mcapdata = future_mcapdata.result()
    print(f"mcapdata: {mcapdata}, type: {type(mcapdata)}")
    age = future_age.result()
    print(f"age: {age}, type: {type(age)}")
    balance = future_balance.result()
    print(f"balance: {balance}, type: {type(balance)}")

    # result.append(transaction)
    # result.append(mcapdata)
    # result.append(age)
    # result.append(balance)
    result = [transaction, mcapdata, age, balance]
    print(f"\nfilter tx tuples execution time: {round(time.time()-start,2)}\n")


    return result


def make_api_calls(transactions, api_key, proxy, header):
    start = time.time()
    results = []
  
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=11) as executor:
        # Create a dictionary of futures with corresponding transactions
        futures_dict = {executor.submit(filter_tx_tuples, transaction, api_key, proxy, header): transaction for i, transaction in enumerate(transactions)}
        
        retries = 0
        # Wait for all futures to complete and retrieve the results
        for future in concurrent.futures.as_completed(futures_dict.keys()):
            try:
                result = future.result()
                print(f"here i print result to debug {result}") #debug line
                results.append(result)
                retries = 0  # reset the retries counter when a request is successful

            except Exception as e:
                error_message = str(e)
                if "Max rate limit reached" in error_message and retries < 10:  # retry up to 10 times
                    wait_time = (2 ** retries) + random.random()  # exponential backoff with jitter
                    time.sleep(wait_time)
                    retries += 1
                    # retry the future
                    transaction = futures_dict[future]  # get the transaction that corresponds to the future
                    futures_dict[executor.submit(filter_tx_tuples, transaction, api_key, proxy, header)] = transaction  # retry with a different key, proxy, and header
                    
                else:
                    print(f"make api calls function | API request error: {e}")
            # Sleep for 0.2 seconds to ensure no more than 5 requests per second
    print(f"\n execution time for: Make API Call {round(time.time()-start,2)}\n")      

    return results


#checks if an address is a contract INFURA
def is_contract_address(address):
   # Connect to Ethereum node using Web3 provider
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
    checksum_address = Web3.to_checksum_address(address)
    code = w3.eth.get_code(checksum_address)
    return len(code) > 2

#get transaction count of (to txs) an address (not contract or token) INFURA
def get_transaction_count(address):
    # Connect to Ethereum node using Web3 provider
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
    checksum_address = Web3.to_checksum_address(address)

    # Get transaction count
    transaction_count = w3.eth.get_transaction_count(checksum_address)
    return transaction_count



def get_effective_transactions(address, api_key, proxy, header):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}

    try:
        response = requests.get(url, proxies={"http:":proxy, "https:":proxy}, headers=headers)
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
                if to_address == address.lower() and from_address != address.lower():
                    if from_address not in address_set and get_transaction_count(from_address) < 4000:
                        address_set.add(from_address)
                        all_transactions.append((tx["hash"], from_address, "in"))
                        

            transaction_count = len(all_transactions)
            liq_removal_count = len(liq_removal_txs)
          
            return all_transactions, transaction_count, liq_removal_txs
    except requests.exceptions.RequestException as e:
        print(f"Etherscan txlist Error: {e}")

    return None, -1, []

# (Analyze_address and analyze_address_hops functions go here...)







def analyze_addressv2(address, hop, max_hops, tx_path, tx_count_per_hop, api_key, proxy, header):
    txList, tx_count, liq_removal_txs = get_effective_transactions(address, api_key, proxy, header)  # Receive liq_removal_txs

    tx_count_per_hop[hop-1] += tx_count  # Update the count
    oldest_wallet = None
    richest_wallet = None
    winning_data = None
    next_hop_addresses = []
    liq_removal_wallet = None  # Initialize liq_removal_wallet


    if tx_count > 0:
        tupleList_chunks = [txList[i:i+5] for i in range(0, len(txList), 5)]
        for item in tupleList_chunks:
            results = make_api_calls(item, api_key, proxy, header)
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
                    liq_removal_wallet = {'tx_path': tx_path, 'hop': hop, 'address': address, 'liquidity_removals': len(liq_removal_txs), 'liq_removal_txs': liq_removal_txs}

    return oldest_wallet, richest_wallet, winning_data, liq_removal_wallet, next_hop_addresses  # Return liq_removal_wallet


def analyze_address(address, hop, max_hops, tx_path, tx_count_per_hop, api_key, proxy, header):

    headers = [f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT5}", f"{USER_AGENT6}"]
    api_keys = [f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY5}", f"{ETHERSCAN_API_KEY6}", f"{ETHERSCAN_API_KEY7}", f"{ETHERSCAN_API_KEY8}", f"{ETHERSCAN_API_KEY9}"]
    proxies =[f"{PROXY1}", f"{PROXY2}", f"{PROXY3}", f"{PROXY4}", f"{PROXY5}"]

    txList, tx_count, liq_removal_txs = get_effective_transactions(address, api_key, proxy, header)  # Receive liq_removal_txs

    tx_count_per_hop[hop-1] += tx_count  # Update the count
    oldest_wallet = None
    richest_wallet = None
    winning_data = None
    next_hop_addresses = []
    liq_removal_wallet = None  # Initialize liq_removal_wallet

    if tx_count > 0:
        tupleList_chunks = [txList[i:i+9] for i in range(0, len(txList), 9)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures_to_item = {}
            for i, item in enumerate(tupleList_chunks):
                future = executor.submit(make_api_calls, item, api_keys[i%9], proxy, headers[i%6])
                futures_to_item[future] = item
            for future in concurrent.futures.as_completed(futures_to_item):
                results = future.result()
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
                        liq_removal_wallet = {'tx_path': tx_path, 'hop': hop, 'address': address, 'liquidity_removals': len(liq_removal_txs), 'liq_removal_txs': liq_removal_txs}

    return oldest_wallet, richest_wallet, winning_data, liq_removal_wallet, next_hop_addresses  # Return liq_removal_wallet



def analyze_address_hops(address, api_key, proxy, header, hop=1, max_hops=5, max_txs=3, tx_path=None, tx_count_per_hop=None):
    if tx_path is None:
        tx_path = []

    if tx_count_per_hop is None:
        tx_count_per_hop = [0] * max_hops  # Initialize only once

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
            if sum(tx_count_per_hop) < max_txs:
                oldest_wallet, richest_wallet, winning_data, liq_removal_wallet, addr_next_hop_addresses = analyze_address(addr, current_hop, max_hops, tx_path, tx_count_per_hop, api_key, proxy, header)  # Receive liq_removal_wallet

                next_hop_addresses.extend(addr_next_hop_addresses)

                if oldest_wallet is not None and (oldest_wallet_per_hop[current_hop-1] is None or oldest_wallet['age'] > oldest_wallet_per_hop[current_hop-1]['age']):
                    oldest_wallet_per_hop[current_hop-1] = oldest_wallet

                if richest_wallet is not None and (richest_wallet_per_hop[current_hop-1] is None or richest_wallet['balance'] > richest_wallet_per_hop[current_hop-1]['balance']):
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




#Main function for this file, it gets executed only if you run this file directly

def main():
 
    address = input("Enter an ethereum contract address: ")
    start = time.time()
    api_key = f"{ETHERSCAN_API_KEY6}"
    list =get_effective_transactions(address, api_key, f"{PROXY2}", f"{USER_AGENT2}")
    print(f"\n\neffective txs: {list}\n\n") 

    

    oldest_wallet_per_hop, richest_wallet_per_hop, winning_data_per_hop, liq_removal_data_per_hop, total_liq_removals, tx_count_per_hop = analyze_address_hops(address, api_key, f"{PROXY6}", f"{USER_AGENT6}", hop=1, max_hops=5, max_txs=90,tx_path = None, tx_count_per_hop=None)

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

    print(f"\nOldest connected wallet: {oldest_wallet_per_hop}")
    print(f"\nRichest connected wallet: {richest_wallet_per_hop}")
    if winning_data_per_hop:
        print(f"\nWinning data: {winning_data_per_hop}")
    print(f"\ntransaction count per hop {tx_count_per_hop}")
    print(f"\nliq removal data {liq_removal_data_per_hop}\n")
    print(f"\n total liq removals {total_liq_removals}")

    print(f"finished after {round(time.time() - start, 2)} seconds")



                    
                    
                        

               
if __name__ == "__main__":
    main()
