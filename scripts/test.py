from web3 import Web3
import time
import os
import requests
from dotenv import load_dotenv
from modules import ethsourcecode
import hashlib


load_dotenv()
infura_key = os.environ['INFURA_API_KEY2']
alchemy_key = os.environ['ALCHEMY_API_KEY']
etherscan_api = os.environ['ETHERSCAN_API_KEY']
proxy = os.environ['WPROXY1']
proxy2 = os.environ['PROXY2']


def main():
    address = input("input the contract address or address here: ")
    print(f"{proxy}, {proxy2}")
    result = ethsourcecode.extract_nametags_and_addresses(address, proxy)
    print(result)
    response = requests.get('https://httpbin.org/ip', proxies={"http": proxy, "https": proxy}, headers = None)
    print(response.json())    
if __name__ == "__main__":
    main()







