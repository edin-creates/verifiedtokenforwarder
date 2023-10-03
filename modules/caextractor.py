import re
import logging
from web3 import Web3
from dotenv import load_dotenv
import os


load_dotenv()
ETHERSCAN_API_KEY = os.environ['ETHERSCAN_API_KEY']
INFURA_API_KEY = os.environ['INFURA_API_KEY']
INFURA_URL = os.environ['INFURA_URL']
ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
MOBULA_API_KEY = os.environ['MOBULA_API_KEY']
MORALIS_API_KEY1 = os.environ['MORALIS_API_KEY_1']
MORALIS_API_KEY2 = os.environ['MORALIS_API_KEY_2']
MORALIS_API_KEY3 = os.environ['MORALIS_API_KEY_3']
MORALIS_API_KEY4 = os.environ['MORALIS_API_KEY_4']


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Function that extracts an ethereum contract address from a text
def extract_contract_address(text):

    cleaned_text = re.sub(r"[^a-zA-Z0-9\s:]", "", text)
    contract_address = None
    pattern = r"(?i)CA\s*:\s*(0x[a-fA-F0-9]{40})"
    match = re.search(pattern, cleaned_text)

    if match:
        contract_address = match.group(1)
        # web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'))
        # checksum_address = web3.to_checksum_address(contract_address)



    return contract_address


test = '''**Scan:** inconclusive (🧐 manual review recommended).

**CA:** `0xe745C89c8c8De21979F851C31400006D99832296

`**Supply:** 10,000,000 (+18 decimals)

🔗 TG 🤷‍♂️ | Web 🤷‍♂️ | Twitter 🤷‍♂️ | [Code](https://etherscan.io/address/0xe745C89c8c8De21979F851C31400006D99832296#code) | [Deployer
](https://etherscan.io/address/0x416259AbbAfB6eA41a51fC63a76F6EC316d5C287)_'''

result = extract_contract_address(test)

logger.info(f"ca:+{result}")
