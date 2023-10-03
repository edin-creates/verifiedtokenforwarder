import requests
import asyncio
import logging
import re
import json
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
import aiohttp
from moralis import evm_api
import os
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
from decimal import Decimal, ROUND_DOWN
from urlextract import URLExtract
import time
import random
import pysnooper
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import httpx
from requests.auth import HTTPBasicAuth


load_dotenv()
ETHERSCAN_API_KEY = os.environ['ETHERSCAN_API_KEY']
ETHERSCAN_API_KEY2 = os.environ['ETHERSCAN_API_KEY2']
ETHERSCAN_API_KEY3 = os.environ['ETHERSCAN_API_KEY3']
ETHERSCAN_API_KEY4 = os.environ['HOPANALYSIS_ETHERSCAN_1']
ETHERSCAN_API_KEY5 = os.environ['HOPANALYSIS_ETHERSCAN_2']
ETHERSCAN_API_KEY6 = os.environ['HOPANALYSIS_ETHERSCAN_3']
ETHERSCAN_EREN1 = os.environ['ETHERSCAN_EREN1']


INFURA_API_KEY = os.environ['INFURA_API_KEY']
INFURA_API_KEY2 = os.environ['INFURA_API_KEY2']
INFURA_API_KEY3 = os.environ['INFURA_API_KEY3']
INFURA_API_KEY4 = os.environ['INFURA_API_KEY4']
INFURA_API_KEY5 = os.environ['INFURA_API_KEY5']
INFURA_API_KEY6 = os.environ['INFURA_API_KEY6']
INFURA_API_KEY7 = os.environ['INFURA_API_KEY7']
INFURA_API_KEY8 = os.environ['INFURA_API_KEY8']
INFURA_API_KEY9 = os.environ['INFURA_API_KEY9']

ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
MOBULA_API_KEY = os.environ['MOBULA_API_KEY']
MORALIS_API_KEY1 = os.environ['MORALIS_API_KEY_1']
MORALIS_API_KEY2 = os.environ['MORALIS_API_KEY_2']
MORALIS_API_KEY3 = os.environ['MORALIS_API_KEY_3']
MORALIS_API_KEY4 = os.environ['MORALIS_API_KEY_4']
MORALIS_API_KEY5 = os.environ['MORALIS_API_KEY_5']

COVALENT_API = os.environ['COVALENT_API_KEY']

#proxies and user agents 
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

USER_AGENT1 = os.environ['USER_AGENT1']
USER_AGENT2 = os.environ['USER_AGENT2']
USER_AGENT3 = os.environ['USER_AGENT3']
USER_AGENT4 = os.environ['USER_AGENT4']
USER_AGENT5 = os.environ['USER_AGENT5']
USER_AGENT6 = os.environ['USER_AGENT6']



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################################### CA Source code and url#############################################################



class CustomClient(httpx.AsyncClient):
    def __init__(self, *args, api_key, proxies=None, headers=None , infuras=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.proxies = proxies
        self.headers = headers
        self.infuras = infuras

#source code etherscan url
def get_etherscan_url(contract_address):
    return f"https://etherscan.io/address/{contract_address}#code"

#get source code text
def get_contract_source_code(contract_address, api_key, header):
    base_url = "https://api.etherscan.io/api"
    headers = {'User-Agent': header}

    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": contract_address,
        "apikey": api_key
    }

    response = httpx.get(base_url, params=params, headers=headers)
   
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1" and data["message"] == "OK":
            source_code = data["result"][0]["SourceCode"]
            source_code_lines = source_code.split("\n")
            return source_code_lines[:40]
            
        
    return None

def add_spaces_around_urls(text):
    try:
        if isinstance(text, list):
            text = ' '.join(text)
        url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
        print(f"add_spaces_around_urls Value of text: {text}")
        print(f" add_spaces_around_urls Type of text: {type(text)}")
        return re.sub(url_pattern, r' \1 ', text)
       

    except Exception as e:
            print(f"Error in add_spaces_around_urls : {e}")

def preprocess_text(text):
    if isinstance(text, list):
        return [t.replace('\\n', '\n').replace('\\r', '\r') for t in text]
    else:
        return text.replace('\\n', '\n').replace('\\r', '\r')

#function that retrives all the social media and organises it from a messy source code
def get_socialmedia_filter(contract_address, api_key, proxy, header):
   

    try:
        extractor = URLExtract()
        text = get_contract_source_code(contract_address, api_key, proxy, header)
        text = preprocess_text(text)
        text_with_spaces = add_spaces_around_urls(text)

        urls = extractor.find_urls(text_with_spaces)
        blacklist = ['github.com','hardhat.org','msg.data','zeppelin.solutions', 'openzeppelin.com', 'readthedocs.io', 'ethereum.org', 'consensys.net', 'Etherscan.io', 'sellTaxes.dev', 'BscScan.com']
        filtered_urls = [url for url in urls if not any(black_domain in url for black_domain in blacklist)]
        
        twitter_links = [url for url in filtered_urls if 'twitter.com' in url or 'x.com' in url]
        discord_links = [url for url in filtered_urls if 'discord.com' in url]
        medium_links = [url for url in filtered_urls if 'medium.com' in url]
        telegram_links = [url for url in filtered_urls if 't.me' in url]
        other_websites = [url for url in filtered_urls if url not in twitter_links + medium_links + telegram_links]
        triple_links = int(bool(telegram_links) and bool(twitter_links) and bool(other_websites))


        social_media_text = ""
        if telegram_links is not None and telegram_links: social_media_text += f"**  ⟹ Telegram :** {', '.join(telegram_links)} \n"
        if twitter_links is not None and twitter_links: social_media_text += f"**  ⟹ Twitter :** {', '.join(twitter_links)} \n"
        if other_websites is not None and other_websites: social_media_text += f"**  ⟹ website(s) :** {', '.join(other_websites)} \n"
        if medium_links is not None and medium_links: social_media_text += f"**  ⟹ Medium :** {', '.join(medium_links)} \n"
        if discord_links is not None and discord_links: social_media_text += f"**  ⟹ Medium :** {', '.join(discord_links)} \n"

        print(f"social media text {social_media_text}")
        
        return telegram_links, twitter_links,discord_links, other_websites, medium_links, triple_links, social_media_text
    
    except Exception as e:
        print(f"Error in get_socialmedia_filter: {e}")
##########################################################################################################################



##########################################################################################################################
#pack of functions giving deployer details
def get_deployer(contract_address, api_key, header):
    start = time.time()
    deployer_address = None
    # Create a comma-separated list of contract addresses
    
    api_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={contract_address}&apikey={api_key}"
    headers = {'User-Agent': header}
        
    try:
        # Send the API request
        response = httpx.get(api_url, headers=headers)
        data = response.json()
        if data['status'] == '1':
            for result in data['result']:
                if result['contractAddress'].lower() == contract_address.lower():
                    deployer_address = result['contractCreator']
                    break  # Exit the loop once the deployer address is found 

        else:
            print("deployer log: API request failed.")

    except httpx.RequestError as e:
        print(f"deployer log: API request error: {e}")
    print(f"this is the deployer address {deployer_address}")
    print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")

    return deployer_address



#uses the covalent API and gives all token balance details
def get_balance_cov(address, min_quote=10000):
    url = f"https://api.covalenthq.com/v1/1/address/{address}/balances_v2/?no-spam=true&no-nft-asset-metadata=false?quote-currency=USD"
    
    # Replace with your actual API key
    API_KEY = f"{COVALENT_API}"
    auth = HTTPBasicAuth(API_KEY, '')
    
    response = requests.get(url, auth=auth)
    data = response.json()
    
    if data["data"]["items"]:
        valuable_tokens = []
        # only check the first two items
        for item in data["data"]["items"][:2]:
            quote = Decimal(item["quote"])
            if quote >= min_quote:
                valuable_tokens.append({
                    "token_address": item["contract_address"],
                    "token_symbol": item["contract_ticker_symbol"],
                    "token_name": item["contract_name"],
                    "quote": quote,
                })
        return valuable_tokens




def get_deployer_details(contract_address, api_key, header):
    start = time.time()
    
    api_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={contract_address}&apikey={api_key}"
    headers = {'User-Agent': header}


    for _ in range(3):  # Retry up to 3 times
        try:
            response = httpx.get(api_url, headers=headers)
            data = response.json()
            if data['status'] == '1':
                for result in data['result']:
                    if result['contractAddress'].lower() == contract_address.lower():
                        deployer_address = result['contractCreator']
                        break
                else:
                    continue  # Continue to the next retry if we didn't break from the loop
                break  # Break from the retry loop if we found the deployer address
            else:
                print("get_deployer_details: API request failed.")
                time.sleep(random.uniform(1, 2))  # Wait for a random time before retrying
        except Exception as e:
            print(f"API request error: {e}")
            time.sleep(random.uniform(1, 2))  # Wait for a random time before retrying
    else:
        return None, None, None  # Return None for everything if all retries failed

    with ThreadPoolExecutor(max_workers=2) as executor:
        balance_future = executor.submit(get_balance, deployer_address, api_key, proxy, header)
        age_future = executor.submit(get_age, deployer_address, api_key, proxy, header)

    balance_eth = balance_future.result()
    deployer_age_days = age_future.result()

    print(f"get_deployer_details finished in {round(time.time()-start,2)}")
    return deployer_address, balance_eth, deployer_age_days
##########################################################################################################################


#get the deployer name from etherscan nametag
def get_address_nametag(address):
    url = f"https://etherscan.io/address/{address}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = httpx.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        title_element = soup.select_one('title')
        if title_element:
            title_text = title_element.text.strip()
            separator = ' | '
            if title_text.count(separator) == 2:
                parts = title_text.split(separator)
                nametag = parts[0].strip()
                print(f"Nametag: {nametag}")
                return nametag
    except Exception as e:
        print(f"get_nametag log error: {e}")
        return None

#get the nametags in bulk to easily identify the funding source Binance or kucoin or.....
def extract_nametags_and_addresses(address):

    check_list = ["binance", "kucoin", "huobi", "fixedfloat", "coinbase", "mexc", "bybit", "kraken", "okx", "bitstamp", "gate", "gemini", "lbank", "pionex", "bitget", "coincheck", "coinw", "bitmart"]

    url = f"https://etherscan.io/txs?a={address}&f=3"
    # Download the HTML from the given URL
    
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
       

    response = httpx.get(url, headers=headers)
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    # find the table containing the transaction details
  
    table = soup.find('table')
    if table is None:
        return {}

    # find all 'a' elements within the table
    a_elements = table.find_all('a')

    # list to hold nametags
    nametags = []

    # iterate through all 'a' elements
    for a in a_elements:
        # check if the element's 'href' attribute starts with '/address/'
        if a.get('href').startswith('/address/'):
            # the nametag is the text within the 'a' element
            nametag = a.text.strip().lower()
            for word in check_list:
                if word in nametag:
                    nametags.append(word)
            



    # count the number of nametags corresponding to each element of the list
    counts = Counter(nametags)

    # return the element of the list with the highest number of nametags
    most_common_nametag = counts.most_common(1)
    if len(counts) > 0:
        result = most_common_nametag[0][0]
    else:
        result = most_common_nametag

    return result

#Get pair address INFURA
def get_pair(contract_address):
    # Connect to the Ethereum network
    web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))

    # Load the Uniswap V2 Factory contract
    factory_address = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
    factory_abi = [
        {
            "constant": True,
            "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}],
            "name": "getPair",
            "outputs": [{"name": "pair", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    factory_contract = web3.eth.contract(address=factory_address, abi=factory_abi)

    # Get the WETH token address
    weth_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    checksum_address = web3.to_checksum_address(contract_address)

    # Get the pair address using the factory contract
    pair_address = factory_contract.functions.getPair(checksum_address, weth_address).call()

    return pair_address

#get token price INFURA
def get_price(contract_address):
    web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
    
    #get the decimals of the token
    checksum_address = web3.to_checksum_address(contract_address)

    # Get the contract ABI for ERC20 tokens
    abi = [             
        {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
        }
    ]
 
    # Create a contract instance
    contract0 = web3.eth.contract(address=checksum_address, abi=abi)

    # Call the totalSupply() function
    try:
        decimals = contract0.functions.decimals().call()
    except Exception as e:
        print(f"error retrieving total supply and/or decimals not an ERC20 token")
        return None

    # Get the pair address using the get_pair function
    pair_address = get_pair(contract_address)
    abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "token0",
            "outputs": [{"name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "token1",
            "outputs": [{"name": "", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [{"name": "_reserve0", "type": "uint112"}, {"name": "_reserve1", "type": "uint112"}, {"name": "_blockTimestampLast", "type": "uint32"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        
    ]
    contract = web3.eth.contract(address=pair_address, abi=abi)
    try:
        token0_address = contract.functions.token0().call()
        token1_address = contract.functions.token1().call()
    except Exception as e:
        print(f'Error retrieving token addresses: {str(e)}')
        return None, None

    eth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    if token0_address.lower() == eth_address.lower():
        reserves = contract.functions.getReserves().call()
        reserve0 = reserves[0]
        reserve1 = reserves[1]
        eth_price = get_ethereum_price()
        token_price = (reserve0 / reserve1) * (10**(decimals - 18)) * eth_price
        liquidity_temporary = ( reserve0 / 10**18 ) * eth_price
        liquidity = smart_format_number(liquidity_temporary)
    elif token1_address.lower() == eth_address.lower():
        reserves = contract.functions.getReserves().call()
        reserve0 = reserves[0]
        reserve1 = reserves[1]
        eth_price = get_ethereum_price()
        token_price = (reserve1 / reserve0) * (10**(decimals - 18)) * eth_price
        liquidity_temporary = ( reserve1 / 10**18 ) * eth_price
        liquidity = smart_format_number(liquidity_temporary)
    else:
        raise ValueError("ETH token not found in the pair")

    return token_price, liquidity

#Calculates the marketcap of a token
def get_marketcap(contract_address):
    start = time.time()
    try:
        price, liquidity = get_price(contract_address)
        tsupply, decimals = get_total_supply(contract_address)
        supply = int(tsupply.replace(',', ''))
        tmcap = price * supply
        mcap = smart_format_number(int(tmcap))
    except Exception as e:
        print(f"no lp or/and not an erc20 token")
        return None, None
    
    print(f"\n get_marketcap finished after {round(time.time() - start, 2)} seconds \n")

    return mcap, liquidity

#ETH PRICE IN USD using coingecko API
def get_ethereum_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "ethereum",
        "vs_currencies": "usd"
    }
    
    response = httpx.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        ethereum_price = data.get("ethereum", {}).get("usd")
        return ethereum_price
    
    return None

#formats numbers to look clean with K M and B suffixes for thousands, millions and billions
def smart_format_number(number):
    # Convert the number to float
    number = float(number)
     # Get the number of digits
    num_digits = len(str(int(abs(number))))

    # Check the number of digits
    if 4 <= num_digits < 7:
        number /= 1000
        suffix = "K"
    elif 7 <= num_digits < 10:
        number /= 1000000
        suffix = "M"
    elif num_digits >= 10:
        number /= 1000000000
        suffix = "B"
    else:
        return str(number)  # No formatting needed

    # Format the number with 2 decimal places
    formatted_number = "{:.2f}".format(number)

    # Add the suffix
    formatted_number += suffix

    return formatted_number


    



async def get_total_supply(contract_address, client):
    start = time.time()
    
    request_kwargs = {
    #"proxy": client.proxies["http://"],
    "headers": client.headers,
    }
    infura_key = f"{INFURA_API_KEY2}"
    print(f"proxy = {client.proxies}, key = {infura_key}")

    provider = AsyncHTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}', request_kwargs=request_kwargs)

    web3 = AsyncWeb3(provider)
    
    # Convert the address to checksum format
    checksum_address = web3.to_checksum_address(contract_address)
    
    # Your ABI definition
    
    # Get the contract ABI for ERC20 tokens
    abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },      
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Create a contract instance
    contract = web3.eth.contract(address=checksum_address, abi=abi)
    
    # Call the totalSupply() and decimals() functions asynchronously
    try:
        total_supply = await contract.functions.totalSupply().call()
        decimals = await contract.functions.decimals().call()
    except Exception as e:
        print(f"error retrieving total supply and/or decimals not an ERC20 token: {e}")
        return None

    t_decimals = int(decimals)
    t_supply = int(total_supply) / (10 ** t_decimals)
    formatted_total_supply = '{:,.0f}'.format(t_supply)
    print(f"\n get_total_supply finished after {round(time.time() - start, 2)} seconds \n")

    return formatted_total_supply, t_decimals


#get namestymbol INFURA
def get_name_symbol(contract_address):
    start = time.time()
    # Connect to the Ethereum network
    web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))  # Replace with your Infura API URL or other Ethereum provider

    # Convert the address to checksum format
    checksum_address = web3.to_checksum_address(contract_address)

    # Get the contract ABI for ERC20 tokens
    abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]

    # Create a contract instance
    contract = web3.eth.contract(address=checksum_address, abi=abi)

    # Call the totalSupply() function and others
    try:
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
    except Exception as e:
        print(f"Error retrieving token details: {e}")
        return None

    print(f"\n get_token_details finished after {round(time.time() - start, 2)} seconds \n")

    return name, symbol



async def get_txcount_etherscan(contract_address, client):
    start = time.time()
    
    api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=500&startblock=0&endblock=99995780&sort=asc&apikey={client.api_key}"
    
    retries = 3
    for _ in range(retries):
        try:
            # Send the API request
            response = await client.get(api_url)
            response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

            data = response.json()
            if data['status'] == '1':
                txcount = len(data['result'])
                print(f"this is the txcount {txcount}")
                print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")
                return txcount
            else:
                print("etherscan txcount log: API request returned a non-success status.")
                return 0
                
        except (httpx.RequestError, httpx.HTTPError) as e:
            print(f"etherscan txcount log: Error occurred during API request: {e}")
            await asyncio.sleep(random.uniform(0.4, 1.5))  # Random sleep before retry

    print("etherscan txcount log: API request failed after all retries.")
    return -1


async def get_txcount_etherscanv1(contract_address, client):
    start = time.time()
    
    api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=500&startblock=0&endblock=99995780&sort=asc&apikey={client.api_key}"
    
    try:
        # Send the API request
        response = await client.get(api_url)
        data = response.json()
        if data['status'] == '1':
            txcount = len(data['result'])
        else:
            print("etherscan txcount log: API request failed.")
            txcount = -1  # Set a default value for txcount in case of failure.

    except httpx.RequestError as e:
        print(f"etherscan txcount log: API request error: {e}")
        txcount = -1  # Set a default value for txcount in case of exception.
    
    print(f"this is the txcount {txcount}")
    print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")

    return txcount


#Calculate the tx count and Volume in usd of a Contract MORALIS
# get_tx_count
async def get_tx_count(contract_address, client):
    api_key = f"{MORALIS_API_KEY3}"
    params = {
        "address": contract_address,
        "chain": "eth",
       # "limit": 1
    }
    try:
        result = await evm_api.token.get_token_transfers(
            api_key=api_key,
            params=params,
            
        )

        txcount = (result["result"])
        print(f"inside get_tx_count that uses moralis txcount: {txcount}")
        return txcount
    except httpx.RequestError as e:
        print(f"Error occurred while fetching transaction count: {e}")
        return -1

# get_balance
async def get_balance(deployer_address, client):
    balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={deployer_address}&tag=latest&apikey={client.api_key}"

    for _ in range(3):  # Retry up to 3 times
        try:
            balance_response = await client.get(balance_url)
            balance_data = balance_response.json()
            balance_wei = int(balance_data["result"])
            w3 = Web3()
            balance_eth = w3.from_wei(balance_wei, "ether")
            return balance_eth
        except Exception as e:
            print(f"Error getting balance: {e}")
            await asyncio.sleep(random.uniform(0.4, 1.5))  # Wait for a random time before retrying

    return None  # Return None if all retries failed


# get_age
async def get_age(deployer_address, client):
    dp_transaction_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={deployer_address}&startblock=0&endblock=99999999&sort=asc&apikey={client.api_key}"

    for _ in range(3):  # Retry up to 3 times
        try:
            dp_transaction_response = await client.get(dp_transaction_url)
            dp_transaction_data = dp_transaction_response.json()

            dp_transactions = dp_transaction_data["result"]
            dp_timestamp = int(dp_transactions[0]["timeStamp"])
            current_timestamp = int(datetime.utcnow().timestamp())
            deployer_age_days = round((current_timestamp - dp_timestamp) / (60 * 60 * 24), 2)
            if deployer_age_days < 1:
                deployer_age_days = round((current_timestamp - dp_timestamp) / (60 * 60 * 24), 2)
            else:
                deployer_age_days = int((current_timestamp - dp_timestamp) / (60 * 60 * 24))

            return max(0, deployer_age_days)
        except Exception as e:
            print(f"Error getting age: {e}")
            await asyncio.sleep(random.uniform(0.4, 1.5))  # Wait for a random time before retrying

    return None  # Return None if all retries failed

    
#returns the contracts deployed by a deployer of a contract in a list


#check if the deployer removed liquidity before
def detect_liquidity_removals(address, api_key, header):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}


    try:
        response = httpx.get(url, headers=headers)
        data = json.loads(response.text)
        if data["status"] == "1":
            transactions = data["result"]
            liquidity_removal_txs = []
            for tx in transactions:
                function_name = tx.get("functionName", "").lower()
                if tx["isError"] == "0" and "remove" in function_name and "liquidity" in function_name:
                    liquidity_removal_txs.append(tx["hash"])
            return len(liquidity_removal_txs), liquidity_removal_txs
    except httpx.RequestError as e:
        print(f"Etherscan txlist Error: {e}")

    return None, []

# batch treatment of all the contracts listed returns the highest contract mcap with more than 300 transactions
async def get_former_contracts_created(address, client):
    api_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=999999999&sort=asc&apikey={client.api_key}"
    print(f"get former contracts created is starting")
    try:
        response = await client.get(api_url)
        data = response.json()
        if data['status'] == '1':
            print(f"yay status 1 of data")
            transactions = data['result']

            contracts = set()

            for tx in transactions:
                if tx["to"] == "":  # Check if contract creation method matches
                    contract = tx['contractAddress']
                    if contract.lower() != address.lower():
                        contracts.add(contract)
                        print(f"got some contracts {contract}")
            return list(contracts)

        else:
            print("get former contracts created: data status 0")
            return []

    except httpx.RequestError as e:
        print(f"API request error: {e}")
        return []
    
async def get_former_contracts_created_and_age(address, client):
    api_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=999999999&sort=asc&apikey={client.api_key}"
    print(f"get former contracts created is starting")
    try:
        response = await client.get(api_url)
        data = response.json()
        if data['status'] == '1':
            print(f"yay status 1 of data")
            transactions = data['result']
            contracts = set()
            for tx in transactions:
                if tx["to"] == "":  # Check if contract creation method matches
                    contract = tx['contractAddress']
                    if contract.lower() != address.lower():
                        contracts.add(contract)
                        print(f"got some contracts {contract}")
            calist= list(contracts)

            dp_transactions = data["result"]
            dp_timestamp = int(dp_transactions[0]["timeStamp"])
            current_timestamp = int(datetime.utcnow().timestamp())
            deployer_age_days = round((current_timestamp - dp_timestamp) / (60 * 60 * 24), 2)
            if deployer_age_days < 1:
                deployer_age_days = round((current_timestamp - dp_timestamp) / (60 * 60 * 24), 2)
            else:
                deployer_age_days = int((current_timestamp - dp_timestamp) / (60 * 60 * 24))

            return calist, max(0, deployer_age_days)

        else:
            print("get former contracts created and age: data status 0")
            return []

    except httpx.RequestError as e:
        print(f"API txlist request error: {e}")
        return []
    
async def filter_pastcoin_contracts_and_age(address, client):
    print(f"filter_pastcoin_contracts called with address={address} and client={client}")

    pastcoins, age = await get_former_contracts_created_and_age(address, client)
    print(f"\n pastcoins found {pastcoins}")
    filtered_contracts = []

    for contract in pastcoins:
        tx_count = await get_txcount_etherscan(contract, client)  # Assume get_tx_count is async now
        print(f"tx count {tx_count}")
        if tx_count is not None:
            if isinstance(tx_count, int):
                if tx_count >= 90:
                    filtered_contracts.append((contract))
            else:
                print(f"Invalid tx_count for contract: {contract}")

    if filtered_contracts:
        max_mcap = 0
        max_contract = None

        for contract in filtered_contracts:
            mcap =  await get_max_marketcap(contract, client)  # Assume get_max_marketcap is async now
            print(f"\nlocal max mcap value {mcap}")

            if mcap > max_mcap:
                max_mcap = mcap
                max_contract = contract

        if max_contract is not None:
            return max_contract, max_mcap, age
        else:
            print("No contract with valid market cap found")

    else:
        print("No contracts with sufficient transaction count and volume found")

    return None, None, age

async def filter_pastcoin_contracts(address, client):
    print(f"filter_pastcoin_contracts called with address={address} and client={client}")

    pastcoins = await get_former_contracts_created(address, client)
    print(f"\n pastcoins found {pastcoins}")
    filtered_contracts = []

    for contract in pastcoins:
        tx_count = await get_txcount_etherscan(contract, client)  # Assume get_tx_count is async now
        print(f"tx count {tx_count}")
        if tx_count is not None:
            if isinstance(tx_count, int):
                if tx_count >= 300:
                    filtered_contracts.append((contract))
            else:
                print(f"Invalid tx_count for contract: {contract}")

    if filtered_contracts:
        max_mcap = 0
        max_contract = None

        for contract in filtered_contracts:
            mcap =  await get_max_marketcap(contract, client)  # Assume get_max_marketcap is async now
            print(f"\nlocal max mcap value {mcap}")

            if mcap > max_mcap:
                max_mcap = mcap
                max_contract = contract

        if max_contract is not None:
            return max_contract, max_mcap
        else:
            print("No contract with valid market cap found")

    else:
        print("No contracts with sufficient transaction count and volume found")

    return None, None




#MOBULA API
async def calculate_max_price(contract_address):
    async with httpx.AsyncClient() as client:
        for _ in range(3):  # Try up to 3 times
            try:
                url = f"https://api.app-mobula.com/api/1/market/history?blockchain=Ethereum&asset={contract_address}"
                headers = {
                    "accept": "application/json",
                    "Authorization": f"{MOBULA_API_KEY}"  # Replace with your authorization token
                }

                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    price_history = data.get("data", {}).get("price_history", [])

                    if price_history:
                        max_price = max(item[1] for item in price_history)
                        return max_price
                    else:
                        return -1  # Return -1 immediately if there's no price history

            except Exception:
                pass

            # If the request fails, wait for a random amount of time between 0.3 and 1.5 seconds before trying again
            await asyncio.sleep(random.uniform(0.4, 1.5))

        return -1  # Return -1 if all attempts fail

#Max Marketcap MOBULA
async def get_max_marketcap(contract_address, client):
    tot_supply, decimals = await get_total_supply(contract_address, client)
    total_supply = int(tot_supply.replace(',', ''))
    max_price_usd = await calculate_max_price(contract_address)
    max_mcap = max_price_usd * total_supply

    return max_mcap
################################################################# MOBULA #################################################












####### main function to run some tests and see if everything is working
async def main():
    deployer_address = input("Enter an Ethereum contract address: ")
    async with httpx.AsyncClient() as client:
        api_key = f"{ETHERSCAN_API_KEY6}"
          # Define your API keys, proxies, and headers
        api_keys = [f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY2}", f"{ETHERSCAN_API_KEY3}", f"{ETHERSCAN_API_KEY4}", f"{ETHERSCAN_API_KEY}"]

        proxies = [f"{PROXY1}", f"{PROXY2}", f"{PROXY3}", f"{PROXY4}", f"{PROXY6}", f"{PROXY7}", f"{PROXY8}", f"{PROXY9}", f"{PROXY10}"]

        headers = [f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT5}", f"{USER_AGENT6}", f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT1}", f"{USER_AGENT2}", f"{USER_AGENT3}", f"{USER_AGENT4}", f"{USER_AGENT5}"]

        infuras = [f"{INFURA_API_KEY}", f"{INFURA_API_KEY4}",f"{INFURA_API_KEY7}",f"{INFURA_API_KEY2}", f"{INFURA_API_KEY5}",f"{INFURA_API_KEY8}",f"{INFURA_API_KEY3}", f"{INFURA_API_KEY6}",f"{INFURA_API_KEY9}"]

        # Create a list of dictionaries, where each dictionary represents a client
        clients = [CustomClient(headers={"User-Agent": user_agent}, proxies={"http://": proxy, "https://": proxy}, api_key=api_key, infuras=infuras) for user_agent, proxy, api_key, infuras in zip(headers, proxies, api_keys, infuras)]
        for i in range(0,11):
            start = time.time()
            totalsupply = await get_age(deployer_address, clients[0])
            print(f"age for proxy {i}: {totalsupply}")
            print(f"finished for PROXY  after {round(time.time() - start , 2)} \n")

    

    

if __name__ == "__main__":
    asyncio.run(main())
 
    
