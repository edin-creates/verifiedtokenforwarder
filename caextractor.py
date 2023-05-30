import re
import logging

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

    return contract_address


test = '''**Scan:** inconclusive (🧐 manual review recommended).

**CA:** `0xe745C89c8c8De21979F851C31400006D99832296

`**Supply:** 10,000,000 (+18 decimals)

🔗 TG 🤷‍♂️ | Web 🤷‍♂️ | Twitter 🤷‍♂️ | [Code](https://etherscan.io/address/0xe745C89c8c8De21979F851C31400006D99832296#code) | [Deployer
](https://etherscan.io/address/0x416259AbbAfB6eA41a51fC63a76F6EC316d5C287)_'''

result = extract_contract_address(test)

logger.info(f"ca:+{result}")
