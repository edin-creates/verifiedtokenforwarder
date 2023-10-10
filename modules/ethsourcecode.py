import requests
import logging
import re
import json
from web3 import Web3
from moralis import evm_api
import os
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
from decimal import Decimal, ROUND_DOWN
from urlextract import URLExtract
from urllib.parse import urlparse
import time
import random
import pysnooper
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import requests
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
INFURA_URL = os.environ['INFURA_URL']
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
USER_AGENT1 = os.environ['USER_AGENT1']
USER_AGENT2 = os.environ['USER_AGENT2']
USER_AGENT3 = os.environ['USER_AGENT3']
USER_AGENT4 = os.environ['USER_AGENT4']
USER_AGENT5 = os.environ['USER_AGENT5']
USER_AGENT6 = os.environ['USER_AGENT6']



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################################### CA Source code and url#############################################################

#source code etherscan url
def get_etherscan_url(contract_address):
    return f"https://etherscan.io/address/{contract_address}#code"

#get source code text
def get_contract_source_code(contract_address, api_key, proxy, header):
    base_url = "https://api.etherscan.io/api"
    headers = {'User-Agent': header}

    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": contract_address,
        "apikey": api_key
    }

    response = requests.get(base_url, params=params, proxies = {"http": proxy, "https": proxy}, headers=headers)
   
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


#the reverse of the smart_format_number function
def smart_parse_number(formatted_number):
    """
    Convert a formatted number string back to a number.
    Converts numbers below a certain threshold to 0.
    
    :param formatted_number: The formatted number string.
    :return: The number.
    """

    threshold = 0.0001  # Set the threshold

    # Handle the case when the formatted_number is already a number
    try:
        number = float(formatted_number)
        # If the number is below the threshold, return 0
        if abs(number) < threshold:
            return 0
        return number
    except ValueError:
        # Continue if it's not a simple float number
        pass

    # Mapping of suffix to the multiplier
    suffix_to_multiplier = {
        "K": 1000,
        "M": 1000000,
        "B": 1000000000
    }

    # Extract the numeric part and the suffix
    numeric_part, suffix = formatted_number[:-1], formatted_number[-1].upper()

    # Check the suffix and multiply the numeric part with the corresponding multiplier
    multiplier = suffix_to_multiplier.get(suffix)
    if multiplier is None:
        raise ValueError(f"Invalid formatted number: {formatted_number}")

    result = float(numeric_part) * multiplier

    # Again check if the result is below the threshold
    if abs(result) < threshold:
        return 0

    return result

#function that retrives all the social media and organises it from a messy source code
def get_socialmedia_filter(contract_address, api_key, proxy, header):
    
    #telegram detection function
    def is_telegram(url):
            if not urlparse(url).scheme:
                url = "http://" + url
            parsed = urlparse(url)
            return parsed.netloc.lower() == 't.me'
    
    #twitter detection function    
    def is_twitter_xcom(url):
        if not urlparse(url).scheme:
            url = "http://" + url
        parsed = urlparse(url)
        return parsed.netloc.lower() == 'x.com'
    
    try:
        extractor = URLExtract()
        text = get_contract_source_code(contract_address, api_key, proxy, header)
        text = preprocess_text(text)
        text_with_spaces = add_spaces_around_urls(text)

        urls = extractor.find_urls(text_with_spaces)
        blacklist = ['github.com', 'stackexchange.com', 'buyfee.marketing', 'sellfee.marketing','soliditylang.org','metamask.io','eth.wiki','github.io','ethers.io','www.smartcontracts.tools' ,'hardhat.org','msg.data','zeppelin.solutions', 'openzeppelin.com', 'readthedocs.io', 'ethereum.org', 'consensys.net', 'Etherscan.io', 'sellTaxes.dev', 'BscScan.com', 'wikipedia.org']
        filtered_urls = set(url for url in urls if not any(black_domain.lower() in url.lower() for black_domain in blacklist))
        
        
        twitter_links = [url for url in filtered_urls if 'twitter.com' in url or is_twitter_xcom(url)]
        discord_links = [url for url in filtered_urls if 'discord.com' in url]
        medium_links = [url for url in filtered_urls if 'medium.com' in url]
        telegram_links = [url for url in filtered_urls if is_telegram(url)]
        other_websites = [url for url in filtered_urls if url not in twitter_links + medium_links + telegram_links + discord_links]
        triple_links = int(bool(telegram_links) and bool(twitter_links) and bool(other_websites))


        social_media_text = ""
        if telegram_links is not None and telegram_links: social_media_text += f"   [▶️](emoji/5816812219156927426) [🔈](emoji/5816796735799824192) **Telegram :** {', '.join(telegram_links)} \n"
        if twitter_links is not None and twitter_links: social_media_text += f"   [▶️](emoji/5816812219156927426) [🌐](emoji/5823584231531483516) **Twitter :** {', '.join(twitter_links)} \n"
        if other_websites is not None and other_websites: social_media_text += f"   [▶️](emoji/5816812219156927426) [🌐](emoji/5823600071370871243) **website(s) :** {', '.join(other_websites)} \n"
        if medium_links is not None and medium_links: social_media_text += f"   [▶️](emoji/5816812219156927426) **Medium :** {', '.join(medium_links)} \n"
        if discord_links is not None and discord_links: social_media_text += f"   [▶️](emoji/5816812219156927426) **Discord :** {', '.join(discord_links)} \n"

        print(f"social media text {social_media_text}")
        
        return telegram_links, twitter_links,discord_links, other_websites, medium_links, triple_links, social_media_text
    
    except Exception as e:
        print(f"Error in get_socialmedia_filter: {e}")
##########################################################################################################################



##########################################################################################################################
#pack of functions giving deployer details
def get_deployer(contract_address, api_key, proxy, header):
    start = time.time()
    deployer_address = None
    # Create a comma-separated list of contract addresses
    
    api_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={contract_address}&apikey={api_key}"
    headers = {'User-Agent': header}
        
    try:
        # Send the API request
        response = requests.get(api_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
        data = response.json()
        if data['status'] == '1':
            for result in data['result']:
                if result['contractAddress'].lower() == contract_address.lower():
                    deployer_address = result['contractCreator']
                    break  # Exit the loop once the deployer address is found 

        else:
            print("deployer log: API request failed.")

    except requests.exceptions.RequestException as e:
        print(f"deployer log: API request error: {e}")
    print(f"this is the deployer address {deployer_address}")
    print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")

    return deployer_address

#uses the etherscan api and only gives value of eth holdings
def get_balance(deployer_address, api_key, proxy, header):
    balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={deployer_address}&tag=latest&apikey={api_key}"
    headers = {'User-Agent': header}

    for _ in range(3):  # Retry up to 3 times
        try:
            balance_response = requests.get(balance_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
            balance_data = balance_response.json()
            balance_wei = int(balance_data["result"])
            w3 = Web3()
            balance_eth = w3.from_wei(balance_wei, "ether")
            return balance_eth
        except Exception as e:
            print(f"Error getting balance: {e}")
            time.sleep(random.uniform(0.2, 1.5))  # Wait for a random time before retrying

    return None  # Return None if all retries failed

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


def get_age(deployer_address, api_key, proxy, header):
    dp_transaction_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={deployer_address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}


    for _ in range(3):  # Retry up to 3 times
        try:
            dp_transaction_response = requests.get(dp_transaction_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
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
            time.sleep(random.uniform(0.2, 1.5))  # Wait for a random time before retrying

    return None  # Return None if all retries failed


def get_deployer_details(contract_address, api_key, proxy, header):
    start = time.time()
    
    api_url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={contract_address}&apikey={api_key}"
    headers = {'User-Agent': header}


    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.get(api_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
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
def get_address_nametag(address, proxy):
    url = f"https://etherscan.io/address/{address}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, proxies={"http": proxy, "https": proxy}, headers=headers)
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
def extract_nametags_and_addresses(address, proxy):

    check_list = ["binance", "kucoin", "huobi", "fixedfloat", "coinbase", "mexc", "bybit", "kraken", "okx", "bitstamp", "gate", "gemini", "lbank", "pionex", "bitget", "coincheck", "coinw", "bitmart", "bitkub"]

    url = f"https://etherscan.io/txs?a={address}&f=3"
    # Download the HTML from the given URL
    
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
       

    response = requests.get(url, proxies={"http": proxy, "https": proxy}, headers=headers)
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



#Get abi function, retrieves the abi of a verified contract in ethereum, uses etherscan
def get_contract_abi(contract_address, etherscan_api_key):
    web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
    contract_address = web3.to_checksum_address(contract_address)
    url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={etherscan_api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == '1':
        return data['result']
    else:
        raise Exception('Failed to fetch contract ABI from Etherscan')

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
    
    response = requests.get(url, params=params)
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

#Calculate the toal supply of a token INFURA
def get_total_supply(contract_address):
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
        }
    ]
 
    # Create a contract instance
    contract = web3.eth.contract(address=checksum_address, abi=abi)

    # Call the totalSupply() function
    try:
        total_supply = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
    except Exception as e:
        print(f"error retrieving total supply and/or decimals not an ERC20 token")
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

#Calculate the tx count and Volume in usd of a Contract MORALIS
def get_tx_count(contract_address):
    api_key = f"{MORALIS_API_KEY5}"
    params = {
        "address": contract_address,
        "chain": "eth",
       # "limit": 1
    }
    try:
        result = evm_api.token.get_token_transfers(
            api_key=api_key,
            params=params,
        )

        txcount = len(result["result"])
        return txcount
    except requests.exceptions.RequestException as e:
        print(f"Error occured while fetching transaction count: {e}")
        return -1
    
#returns the contracts deployed by a deployer of a contract in a list
def get_former_contracts_created(address, api_key, proxy, header):
    #check all the contracts created by the deployer
    api_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=999999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}

    try:
        # Send the API request
        response = requests.get(api_url, proxies={"http":proxy, "https":proxy}, headers=headers )
        data = response.json()
        if data['status'] == '1':
            transactions = data['result']

            contracts = set()

            for tx in transactions:
                if tx["to"] == "":  # Check if contract creation method matches
                    contract = tx['contractAddress']
                    if contract.lower() != address.lower():
                        contracts.add(contract)

            return list(contracts)

        else:
            print("gfcc: API request failed.")
            return []

    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return []

#check if the deployer removed liquidity before
def detect_liquidity_removals(address, api_key, proxy, header):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}


    try:
        response = requests.get(url, proxies={"http": proxy, "https":proxy}, headers=headers)
        data = json.loads(response.text)
        if data["status"] == "1":
            transactions = data["result"]
            liquidity_removal_txs = []
            for tx in transactions:
                function_name = tx.get("functionName", "").lower()
                if tx["isError"] == "0" and "remove" in function_name and "liquidity" in function_name:
                    liquidity_removal_txs.append(tx["hash"])
            return len(liquidity_removal_txs), liquidity_removal_txs
    except requests.exceptions.RequestException as e:
        print(f"Etherscan txlist Error: {e}")

    return None, []

def gfcc(contract_address, api_key, proxy, header):
    #get the deployer address
    deployer = get_deployer(contract_address, api_key, proxy, header)
    print(f"Deployer address: {deployer}")  # Print the deployer address


    # Check if deployer is a valid Ethereum address
    if not Web3.is_address(deployer):
        print(f"gfcc: Invalid Ethereum address: {deployer}")
        return []
    #check all the contracts created by the deployer
    api_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={deployer}&startblock=0&endblock=999999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}

    try:
        # Send the API request
        response = requests.get(api_url, proxies={"http": proxy, "https":proxy}, headers=headers)

        data = response.json()
        if data['status'] == '1':
            transactions = data['result']

            contracts = set()

            for tx in transactions:
                if tx["to"] == "":  # Check if contract creation method matches
                    contract = tx['contractAddress']
                    if contract.lower() != contract_address.lower():
                        contracts.add(contract)

            return list(contracts)

        else:
            print("gfcc: API request failed.")
            return []

    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return []
    
#generic retry function    
def retry_on_failure(func, max_retries=3, delay=3):
    """A simple retry mechanism."""
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            retries += 1
            if retries < max_retries:
                print(f"Error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed after {max_retries} retries.")
                raise
# batch treatment of all the contracts listed returns the highest contract mcap with more than 300 transactions
def filter_pastcoin_contracts(address, api_key, proxy, header):
    pastcoins = retry_on_failure(lambda: get_former_contracts_created(address, api_key, proxy, header)) #point of potential failure 1
    filtered_contracts = []
    
    for contract in pastcoins:
        tx_count = retry_on_failure(lambda: get_tx_count(contract))  #point of potential failure 2
        
        
        if tx_count is not None:
            
            # Check if tx_count and volume are valid numeric values
            if isinstance(tx_count, int):
                if tx_count >= 90:
                    filtered_contracts.append((contract))
            else:
                print(f"Invalid tx_count for contract: {contract}")

    if filtered_contracts:
        max_mcap = 0
        max_contract = None
        
        for contract in filtered_contracts:
            mcap = retry_on_failure(lambda: get_max_marketcap(contract))  #point of potential failure 3
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

#similar to filter pastcoin but doesnt include the contract address we're analysing in the results to avoid redundancy
# def fpc(address):
#     start= time.time()
    

#     pastcoins = gfcc(address)
#     contracts_deployed_count = len(pastcoins)
#     filtered_contracts = []
    
#     # Define a function to get the transaction count for a contract
#     def get_valid_tx_count(contract):
#         tx_count = get_tx_count(contract)
#         if tx_count is not None and isinstance(tx_count, int) and tx_count >= 300:
#             return contract
#         else:
#             print(f"Invalid tx_count for contract: {contract}")
#             return None

#     # Create a ThreadPoolExecutor with two workers
#     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#         # Use a list to keep track of the tasks
#         tasks = [executor.submit(get_valid_tx_count, contract) for contract in pastcoins]

#         # Wait for all tasks to complete
#         for future in concurrent.futures.as_completed(tasks):
#             try:
#                 result = future.result()  # Get the result of the task
#                 if result is not None:
#                     filtered_contracts.append(result)
#             except Exception as e:
#                 print(f"Exception occurred during task execution: {e}")

#     if filtered_contracts:
#         max_mcap = 0
#         max_contract = None
#         contracts_deployed_count = 0
        
#         for contract in filtered_contracts:
#             mcap = get_max_marketcap(contract)
#             print(f"\nlocal max mcap calculated: {mcap}")
            
#             if mcap > max_mcap:
#                 max_mcap = mcap
#                 max_contract = contract
        
#         if max_contract is not None:
#             print(f"fpc finished in {round(time.time()-start,2)}")
#             return max_contract, max_mcap , contracts_deployed_count
#         else:
#             print("No contract with valid market cap found")
#             return max_contract, max_mcap , contracts_deployed_count

        
#     else:
#         print("No contracts with sufficient transaction count and volume found")
#         print(f"fpc finished in {round(time.time()-start,2)}")

#         return "No valid contract found", 0 , 0 



#function that analyses the addresses other than deployer, and return the number of real txs with txcount > 300, the lenght of filtered txs is used in the forwarder to setup condition on which pastcoin data to post so dont change it without checking there too
def fpc(address, api_key, proxy, header):
    start = time.time()
    
    pastcoins = retry_on_failure(lambda: gfcc(address, api_key, proxy, header)) #point of potential failure 1
    contracts_deployed_count = len(pastcoins)
    filtered_contracts = []

    # Modify the function to return tx_count too
    def get_valid_tx_count(contract):
        tx_count = retry_on_failure(lambda: get_tx_count(contract))  #point of potential failure 2
        if tx_count is not None and isinstance(tx_count, int) and tx_count >= 90:
            return (contract, tx_count)
        else:
            print(f"Invalid tx_count for contract: {contract}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        tasks = [executor.submit(get_valid_tx_count, contract) for contract in pastcoins]

        for future in concurrent.futures.as_completed(tasks):
            try:
                result = future.result()  # Get the result of the task
                if result is not None:
                    filtered_contracts.append(result)
            except Exception as e:
                print(f"Exception occurred during task execution: {e}")

    if filtered_contracts:
        # Sort contracts by tx_count in descending order
        filtered_contracts.sort(key=lambda x: x[1], reverse=True)

        max_mcap = 0
        max_contract = None
        
        for contract, tx_count in filtered_contracts:
            mcap = retry_on_failure(lambda: get_max_marketcap(contract))  #point of potential failure 3
            print(f"\nlocal max mcap calculated: {mcap}")
            
            if mcap > max_mcap:
                max_mcap = mcap
                max_contract = contract

        if max_contract is not None:
            print(f"fpc finished in {round(time.time()-start,2)}")
            return max_contract, max_mcap , contracts_deployed_count, len(filtered_contracts) 
        else:
            print("No contract with valid market cap found")
            return filtered_contracts[0][0], 0, contracts_deployed_count, len(filtered_contracts)  # return contract with highest tx_count

    else:
        print("No contracts with sufficient transaction count and volume found")
        print(f"fpc finished in {round(time.time()-start,2)}")

        return "No valid contract found", 0 , 0 , 0


################################################################# MOBULA #################################################
#MOBULA MAX PRICE FAST FUNCTION
# def calculate_max_price(contract_address):
#     try:
#         url = f"https://api.app-mobula.com/api/1/market/history?blockchain=Ethereum&asset={contract_address}"
#         headers = {
#             "accept": "application/json",
#             "Authorization": f"{MOBULA_API_KEY}"  # Replace with your authorization token
#         }

#         response = requests.get(url, headers=headers)

#         if response.status_code == 200:
#             data = response.json()
#             price_history = data.get("data", {}).get("price_history", [])

#             if price_history:
#                 max_price = max(item[1] for item in price_history)
#                 return max_price
#     except Exception:
#         pass

#     return -1


#MOBULA API
def calculate_max_price(contract_address):
    for _ in range(3):  # Try up to 3 times
        try:
            url = f"https://api.app-mobula.com/api/1/market/history?blockchain=Ethereum&asset={contract_address}"
            headers = {
                "accept": "application/json",
                "Authorization": f"{MOBULA_API_KEY}"  # Replace with your authorization token
            }

            response = requests.get(url, headers=headers)

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

        # If the request fails, wait for a random amount of time between 1 and 5 seconds before trying again
        time.sleep(random.uniform(0.3, 1.5))

    return -1  # Return -1 if all attempts fail







#Max Marketcap
def get_max_marketcap(contract_address):

    tot_supply, decimals =  get_total_supply(contract_address)
    total_supply = int(tot_supply.replace(',',''))
    max_price_usd = calculate_max_price(contract_address)
    max_mcap = max_price_usd * total_supply

    return max_mcap
################################################################# MOBULA #################################################



def detect_liquidity_removalsv2(address, api_key, proxy, header):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
    headers = {'User-Agent': header}
    try:
        response = requests.get(url, 
                                proxies={"http": proxy, "https": proxy},
                                headers=headers)
        
        data = json.loads(response.text)
        if data["status"] == "1":
            transactions = data["result"]
            liquidity_removal_txs = []
            for tx in transactions:
                function_name = tx.get("functionName", "").lower()
                if tx["isError"] == "0" and "remove" in function_name and "liquidity" in function_name:
                    liquidity_removal_txs.append(tx["hash"])
            return len(liquidity_removal_txs), liquidity_removal_txs
    except requests.exceptions.RequestException as e:
        print(f"Etherscan txlist Error: {e}")

    return None, []

def get_txcount_etherscan(contract_address, api_key, proxy, header):
        start = time.time()
        # Create a comma-separated list of contract addresses
        
        api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=500&startblock=0&endblock=27025780&sort=asc&apikey={api_key}"
        headers = {'User-Agent': header}
            
        try:
            # Send the API request
            response = requests.get(api_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
            data = response.json()
            if data['status'] == '1':
                txcount = len(data['result'])
                    
            else:
                print("etherscan txcount log: API request failed.")

        except requests.exceptions.RequestException as e:
            print(f"etherscan txcount log: API request error: {e}")
        print(f"this is the txcount {txcount}")
        print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")

        return txcount







####### main function to run some tests and see if everything is working
def main():
    contract_address = input("Enter an Ethereum contract address: ")
    start = time.time()
    #lpremove = detect_liquidity_removalsv2(deployer_address, f"{ETHERSCAN_EREN1}",f"{PROXY2}", f"{USER_AGENT2}")
    def get_txcount_etherscan(contract_address, api_key, proxy, header):
        start = time.time()
        # Create a comma-separated list of contract addresses
        
        api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=500&startblock=0&endblock=27025780&sort=asc&apikey={api_key}"
        headers = {'User-Agent': header}
            
        try:
            # Send the API request
            response = requests.get(api_url, proxies = {"http": proxy, "https": proxy}, headers=headers)
            data = response.json()
            if data['status'] == '1':
                txcount = len(data['result'])
                    
            else:
                print("etherscan txcount log: API request failed.")

        except requests.exceptions.RequestException as e:
            print(f"etherscan txcount log: API request error: {e}")
        print(f"this is the txcount {txcount}")
        print(f"\n get_deployer finished after {round(time.time() - start, 2)} seconds \n")

        return txcount

    txcount = get_txcount_etherscan(contract_address, f"{ETHERSCAN_API_KEY}",None,f"{USER_AGENT1}")
    print(f"p1 lp removals {txcount}")
    print(f"finished after {round(time.time() - start , 2)}")

    

    

if __name__ == "__main__":
    main()
