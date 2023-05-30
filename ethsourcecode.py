import requests
import logging
import re

import os
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.environ['ETHERSCAN_API_KEY']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def get_etherscan_url(contract_address):
    return f"https://etherscan.io/address/{contract_address}#code"


def get_contract_source_code(contract_address):
    base_url = "https://api.etherscan.io/api"
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": contract_address,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1" and data["message"] == "OK":
            source_code = data["result"][0]["SourceCode"]
            source_code_lines = source_code.split("\n")
            return source_code_lines[:40]
            
        
    return None


def filter_links(lines):
    urls = []
    for line in lines:
        urls_in_line = re.findall(r'(?:https?://)?(?:www\.)?(\S+\.(?:me|com|app|net|dog)(?:/\S*)?)', line)
        urls.extend(urls_in_line)
    return urls

#main
def main():
    contract_address = input("Enter an Ethereum contract address: ")
    etherscan_url = get_etherscan_url(contract_address)
    source_code_snippet = get_contract_source_code(contract_address)
    logger.info(source_code_snippet)

    if source_code_snippet:
        filtered_lines = filter_links(source_code_snippet)
        if filtered_lines:
            print("Lines containing a website or a Telegram username:\n" +
                  "\n".join(filtered_lines))
        else:
            print(
                "No lines containing a website or a Telegram username were found in the source code.")
    else:
        print("Unable to fetch the source code.")


if __name__ == "__main__":
    main()
