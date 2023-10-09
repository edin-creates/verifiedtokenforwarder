from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime
from modules import asyncioethsourcecode, ethsourcecode
import asyncio
from asyncio import Queue
from aiolimiter import AsyncLimiter
import web3
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from itertools import cycle
from telethon import TelegramClient, events
from telethon.errors.common import InvalidBufferError
from telethon.extensions import markdown
from telethon import types
from pymongo import MongoClient, IndexModel, ASCENDING
import requests
import httpx
import logging
import re
import concurrent.futures
import time
import random




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


# Your API ID and API hash from https://my.telegram.org, here ia m using ELEMENTOR acc
API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']

source_channel = int(os.environ['SOURCE_CHANNEL'])
target_verified = int(os.environ['TARGET_CHANNEL_VERIFIED'])
target_deployed = int(os.environ['TARGET_CHANNEL_DEPLOYED'])
target_longlock = int(os.environ['TARGET_CHANNEL_LONGLOCKS'])
target_burn = int(os.environ['TARGET_CHANNEL_BURN'])
target_call = int(os.environ['TARGET_CHANNEL_CALL'])

mongodbusername = os.environ['mongodbUsername']
mongodbpassword = os.environ['mongodbPassword']
#custom markdwon to use custom emojis and spoilers in telethon
class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities
    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)
    

# Extract Telegram groups from environment variables and split into a list
TELEGRAM_GROUPS = os.environ.get('TELEGRAM_GROUPS').split(',')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)

class Customclient(httpx.AsyncClient):
    def __init__(self, *args, api_key, proxies=None, headers=None , infuras=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.proxies = proxies
        self.headers = headers
        self.infuras = infuras

# MongoDb database manager class that handles connections to the tokens database
class DatabaseManager:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['tokenDatabase']
        self.tokens = self.db['tokens']
        self.channels = self.db['channels']
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
        # Perform a case-insensitive query by using the $regex operator and the $options: 'i' modifier.
        query = {"_id": {"$regex": f"^{contract_address}$", "$options": 'i'}}
        
        return self.tokens.find_one(query)

    
    
    def get_channel_data(self, chat_id):
        """
        Retrieve data for a specific token by contract address.
        
        :param contract_address: The contract address of the token.
        :return: The data for the token, or None if no matching token was found.
        """
        return self.channels.find_one({"_id": chat_id})
        
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
channels = database_manager.channels
# Fetch token addresses
def get_tokens_from_pair(pair_address):
    # Set up Web3 connection
    infura_url = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
    w3 = Web3(Web3.HTTPProvider(infura_url))

    # Uniswap/Sushiswap Pair ABI
    pair_abi = [{
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }, {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]
    pair_address = w3.to_checksum_address(pair_address)
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    return token0_address, token1_address

def extract_relevant_address_from_text(text):
    # 1. Search for Contract Addresses Not Attached to Specific URLs
    ethereum_address_not_attached_pattern = r"(?<!/)(?!0x000000000000000000000000000000000000dEaD)(?<!dexview\.com/eth/)(?<!defined\.fi/eth/)(?<!dexscreener\.com/ethereum/)(0x[a-fA-F0-9]{40})"

    # 2. Search for Contract Addresses Attached to Specific URLs
    ethereum_address_attached_pattern = r"(/ether/pair-explorer/|dexview\.com/eth/|defined\.fi/eth/|dexscreener\.com/ethereum/)(0x[a-fA-F0-9]{40})"

    # Search for contract addresses not directly attached to specific URLs
    match_not_attached = re.search(ethereum_address_not_attached_pattern, text)
    if match_not_attached:
        return match_not_attached.group(1)
    
    # Search for contract addresses directly attached to specific URLs
    match_attached = re.search(ethereum_address_attached_pattern, text)
    if match_attached:
        # For demonstration purposes, returning the pair address.
        # In practice, you'd use this address to interact with Ethereum to fetch the actual token address.
        pair_address =  match_attached.group(2)
        if pair_address:
            WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # Mainnet WETH address
            # 3. Resolve Pair to Token
            token0_address, token1_address = get_tokens_from_pair(pair_address)
            if token0_address.lower() == WETH_ADDRESS.lower():
                return token1_address
            elif token1_address.lower() == WETH_ADDRESS.lower():
                return token0_address
            else:
                # Neither of the tokens in the pair is WETH.
                # Handle this case as you see fit. For now, we return None.
                return None
    
    # If no relevant address is found, return None
    return None

# Convert the list of dictionaries into a single dictionary for easy lookup

TELEGRAM_GROUPS = [{1636261655: 'duckscallseth'}, {1795429779: 'mrpredatorcall'}, {1678344669: 'DoxxedChannel'}, {1628307296: 'FullofEth'}, {1884815563: 'astrals_gambles'}, {1733712570: 'nycdegendiary'}, {1710998709: 'CryptoMessiahOfficial'}, {1751420997: 'falcongrowcalls'}, {1587879377: 'degensgems'}, {1755285732: 'dontspendmyfortuneonrug'}, {1684991075: 'BossyGambles'}, {1696188050: 'CarnagecallzzGambles'}, {1162128920: 'cryptogems555'}, {1787043883: 'thorshammergems'}, {1410604349: 'apewizardcalls'}, {1645327841: 'waldosalpha'}, {1870127953: 'watisdes'}, {1618011108: 'doxxedguy'}, {1716733148: 'CryptoKidcalls'}, {1784631341: 'CobraGems'}, {1662041785: 'arcanegems'}, {1755052940: 'dr_crypto_channel'}, {1694295613: 'zer0xtrading'}, {1741733092: 'apeguardiancalls'}, {1177366431: 'ProwerCalls'}, {1749650558: 'hualiuen'}, {1713107960: 'zerotwocalls'}, {1850979374: 'cryptowhalecalls7'}, {1666612474: 'caesars_gambles'}, {1774262252: 'sersgemsnipes'}, {1628177089: 'explorer_gems'}, {1820804438: 'venom_gambles'}, {1601300719: 'piggiesCalls'}, {1584715114: 'Safehavencalls'}, {1873230762: 'aladdincall'}, {1780798172: 'Empire100xCalls'}, {1659327836: 'TwanRaidsAlfa'}, {1660459941: 'hodlersgems'}, {1641270416: 'nagatogemcalls'}, {1677530578: 'mrcrypt100xcalls'}, {1500874400: 'niksgambles'}, {1695534644: 'jccalls'}, {1766480253: 'PythagorasGaMbLeS'}, {1507140649: 'asrafreview'}, {1714349746: 'axe_calls'}, {1662909092: 'QuartzETH'}, {1714005506: 'dialgacalls'}, {1218247352: 'luigiscalls'}, {1609073900: 'gubbinscalls'}, {1594520113: 'VirusCalls'}, {1788948325: 'cryptoriskhunter'}, {1674129622: 'wifechangingcallss'}, {1611974309: 'CharlesCalls'}, {1537017945: 'charizardcalls'}, {1423895590: 'TripleXATH'}, {1407455116: 'kingdawgscalls'}, {1873023137: 'UniqueAlphacalls'}, {1615290231: 'yooshicalls'}, {1516481069: 'ethplayinsiderrsir'}, {1712900374: 'HellsingCalls'}, {1783503706: 'bruiserscalls'}, {1613763999: 'gemhunter100xcalls'}, {1581600119: 'zorrogems'}, {1873800012: 'zerotoherogambles'}, {1712294373: 'HermitsCalls'}, {1415271395: 'bobsgems'}, {1677386684: 'Bossy_Callz'}, {1551859299: 'pika_microcap'}, {1732891794: 'GabbensCalls'}, {1724572873: 'jammas100x'}, {1471369538: 'gollumsgems'}, {1603074695: 'Investergram'}, {1844099826: 'bigbullscallz'}, {1582491639: 'moneymancalls1'}, {1542004725: 'cryptobitbull_channel'}, {1700113598: 'KhronosXCall'}, {1793824247: 'earlycallsby0xEly'}, {1718703340: 'batman_gem'}, {1198046393: 'PowsGemCalls'}, {1539467451: 'DaydreamersCryptoHub'}, {1771480507: 'capcalls'}, {1657214410: 'HeliosGem'}, {1622263580: 'CyclopsCrypto'}, {1763265784: 'MarkDegens'}, {1677625475: 'batmansafucalls'}, {1635741540: 'nomsgems'}, {1743089197: 'mhotcallserc'}, {1560066094: 'cryptoqueencalls'}, {1158873476: 'bunnycalls'}, {1616963546: 'kobesgambles'}, {1783206841: 'DeFiGreco'}, {1781858999: 'valhallacalls'}, {1496663342: 'cryptofrogsgems'}, {1683370043: 'thecallercrosschain'}, {1697697574: 'mad_apes_call'}, {1792176742: 'gorillascalls'}, {1541757109: 'BiDaoPD'}, {1860403732: 'somebasedchadreal'}, {1781662296: 'KingDawgsDegenCalls'}, {1568396440: 'cryptachcalls'}, {1783469467: 'richkidcalls'}, {1947677551: 'dogenmanreal'}, {1673911213: 'ballcalls'}, {1870943935: 'cryptoheatplays'}, {1975392115: 'frenzgems'}, {1616418861: 'eslamcrypto'}, {1865359930: 'tugougan_eth'}, {1529480805: 'peyosdegenhub'}, {1452778226: 'Luffysgemcalls'}, {1235977593: 'gongfucalls'}, {1977494876: 'pepegambleeth'}, {1601652682: 'ObitosCalls'}, {1979271631: 'SHYROSHIGAMBLES'}, {1742181648: 'jakefam'}, {1674414708: 'cryptodegen_1000x'}, {1663508721: 'ourcryptohood'}, {1535357377: 'bluemooncalls'}, {1701715499: 'doxxedgamble'}, {1877172822: 'spacemancallz'}, {1518914791: 'TOREsafucall'}, {1654634851: 'NatsuCryptoGems'}, {1925893509: 'hysteriacalls'}, {1197297384: 'maythouscalls'}, {1442000870: 'TBGgambLes'}, {1528638903: 'ryoshigems'}, {1730120280: 'Pika_Review'}, {1584308798: 'dstrends_ethereum'}, {1208298070: 'romeotradescalls'}, {1713964244: 'fexirgamble'}, {1794564478: 'boredapegamble'}, {1650343718: 'LionCALL'}, {1699794892: 'BalineseCalls'}, {1962610706: 'Source'}, {1237108606: 'BrodyCalls'}, {1514821272: 'Carnagecallzz'}, {1777949553: 'CryptoGemsCom'}, {1774485937: 'cryptomobscall'}, {1911404927: 'shithubbyjugger'}, {1343334089: 'Joe420Calls'}, {1973702078: 'HenryGems'}, {1688794358: 'ChineseDragonCalls'}, {1518121187: 'mcwhalescalls'}, {1758451787: 'littlebegod'}, {1684601461: 'boredape_calls'}, {1707625074: 'carsoscalls'}, {1717211000: 'sigcalls'}, {1556643280: 'geelycalls'}, {1672501396: 'gEmsgAmbleseth'}, {1949496645: 'godhandcall'}, {1941255109: 'totaloneth'}, {1772411310: 'NightkrawlerGems'}, {1559905151: 'stureview'}, {1579547727: 'terps_x100_calls'}, {1844498543: 'shanks_calls'}, {1662205299: 'luffychancalls'}, {1725383490: 'degenalertstg'}, {1905125715: 'ryoshigamble'}, {1850785851: 'elon_calls3'}, {1948082809: 'dogehomes'}, {1766948410: 'StacksAlpha'}, {1808237948: 'hitman007calls'}, {1507693512: 'Cryptic_Maestro'}, {1614969455: 'one_vk'}, {1506439617: 'phillipscalls'}, {1620856213: 'veigarcalls'}, {1582651667: 'crypt0coc0'}, {1676655571: 'AnimeGems'}, {1641158969: 'InApeWeTrust'}, {1692756070: 'PythagorasDev'}, {1733654225: 'RiskyGemsHuntersCalls'}, {1522389056: 'sapphirecalls'}, {1377830727: 'theillestshills'}, {1797950401: 'gogetacalls'}, {1598760387: 'raven_calls420'}, {1451577025: 'eezzyjournal'}, {1691606433: 'avrugs'}, {1611231161: 'Crizalcallsx100'}, {1863645036: 'asianwhaleseth'}, {1732329117: 'printspress'}, {1067047613: 'satoshidegen'}, {1507454480: 'ottomangempire'}, {1903316574: 'x666calls'}, {1539955866: 'mooneagle_call'}, {1647209191: 'nomadscalls'}, {1796683207: 'dreamcalls100x'}, {1665621266: 'doraemon_call'}, {1228469908: 'cryptomoonshotss'}, {1604670907: 'theapesgemcalls'}, {1718301453: 'pythoncall'}, {1962710770: 'mrwizardloungecalls'}, {1659455616: 'shutupandprint'}, {1869777491: 'marine_cryptocalls'}, {1925822912: 'Jelitics2X'}, {1575899304: 'knucklesprospercalls'}, {1822637876: 'pepecoincalls'}, {1605011371: 'julzlabs'}, {1428094316: 'gvrcall'}, {1614896791: 'achillesgambles'}, {1740748463: 'mackcalls'}, {1523523939: 'RektSeals'}, {1652789906: 'Green_Apes_Calls'}, {1693174179: 'marshmellow100xcalls'}, {1778331613: 'BROTHERSMARKETINGCHANNEL1'}, {1810322820: 'moetaerc'}, {1668334470: 'zeppelinsbagofgemz'}, {1515849943: 'lowtaxethx'}, {1584920993: 'cryptoyamscalls'}, {1711812162: 'Chadleycalls'}, {1900737447: 'savascalls'}, {1829703638: 'nexusproportal'}, {1655191094: 'PapasCall'}, {1539956400: 'apezone'}, {1762635317: 'trafalgarlawcalls'}, {1816559813: 'firehuntersbsceth'}, {1758611100: 'mad_apes_gambles'}, {1594951131: 'btokchina'}, {1887840067: 'sugarydick'}, {1675680183: 'EmporiumTools'}, {1629431557: 'paradoxes1'}, {1727929287: 'HarleyQuinngamble'}, {1687370328: 'waynechannel'}, {1822229709: 'GabbensGambles'}, {1378126404: 'calls1000xgemsking'}, {1732271814: 'witcher_call'}, {1875835628: 'Bassiecalls'}, {1554385364: 'sultanplays'}, {1225991487: 'bagcalls'}, {1758505999: 'blockchainbrotherscalls'}, {1750748748: 'wechatcalls'}, {1810124798: 'Maestrosdegen'}, {1772190161: 'moonshotcap'}, {1639711365: 'Captain609'}, {1666174805: 'esplays'}, {1822983307: 'HouseAtreidesTG'}, {1854608645: 'archercallz'}, {1549666977: 'TheDonsCalls'}, {1335118230: 'cryptofightersystems'}, {1624019552: 'meliodas100x'}, {1715502498: 'hellsinggamble'}, {1386723491: 'senzu_calls'}, {1616041469: 'moongemssignal'}, {1532098798: 'memecoinlounge'}, {1860207910: 'estplays'}, {1934775636: 'zaynrichorekt'}, {1821039874: 'emilianscalls'}, {1720016839: 'johnwickmemesafari'}, {1700527141: 'notxoraboat'}, {1593378382: 'hypemanalexcalls'}, {1611517290: 'newtokenmarketannouncement'}, {1194831964: 'shillseals'}, {1294574142: 'crypto_millennial'}, {1978870719: 'alphaintelcalls'}, {1585921347: 'omeglecalls'}, {1569325189: 'themanagercalling'}, {1829968037: 'brookcalls'}, {1885046233: 'brinksreports'}, {1598801501: 'doctoreclub'}, {1613789579: 'thewizardsgems'}, {1769975766: 'whodis6964'}, {1706563666: 'zombiecalls1'}, {1514707080: 'conquerorcalls'}, {1519395163: 'monstercallss'}, {1842612932: 'doctoregems'}, {1838340671: 'avengersalphacalls'}, {1722329321: 'moocalls'}, {1721146631: 'kobescalls'}, {1875535682: 'degenmemeee'}, {1592516639: 'regaltosdefi'}, {1784657328: 'enerucalls'}, {1738001944: 'metawhalegems'}, {1513157090: 'stubbornplays'}, {1966824234: 'ishfishes'}, {1584420389: 'markgems'}, {1588764253: 'vitaiikcalls'}, {1751141212: 'decryptaner'}, {1711873691: 'legendcall'}, {1831026872: 'hermesdegens'}, {1846532905: 'insidorgems'}, {1968004868: 'madaras_alpha_calls'}, {1603469217: 'ziongems'}, {1907838158: 'best_daily_tokens'}, {1763658798: 'thesolitaireprestige'}, {1915603814: 'wingsinsider'}, {1361569221: 'infinitewhale'}, {1500214409: 'gemsmineeth'}, {1925306887: 'cryptoprophetcalls'}, {1775057894: 'cryptolord100xcalls'}, {1786131402: 'popeye_calls'}, {1574483612: 'comet_calls'}, {1813773143: 'asia_tiger_pump'}, {1695887507: 'bunnygambles'}, {1905882116: 'alphaethgamble'}, {1646594948: 'seizememe'}, {1800674874: 'big_apes_call'}, {1663368518: 'wencaleb'}, {1951458912: 'catboycalls'}, {1446663512: 'honeycalls'}, {1806092611: 'joyboydegen'}, {1655443406: 'michacalls'}, {1370840045: 'simpscalls'}, {1707008676: 'yummycalls'}, {1533974431: 'clowncalls'}, {1671525878: 'whalevomitcalls'}, {1797075549: 'karma999calls'}, {1626404755: 'katrincalls'}, {1769722814: 'donalddarkmoon'}, {1925213644: 'doctoredegens'}, {1526108028: 'saviourcalls'}, {1915368269: 'carnage_gambles'}, {1888727053: 'cryptodegen_call'}, {1523555663: 'knightgamble'}, {1689659030: 'multihunterx'}, {1916614360: 'trinity_calls'}, {1640163108: 'curlycurrycalls'}, {1740307978: 'ryoshi_calls'}, {1614830768: 'whaledegen_ultra'}, {1624555935: 'ndranghetaethgems'}, {1952788786: 'ramjofficialeth'}, {1956076244: 'shynobi_gems'}, {1627588799: 'maybachcalls'}, {1362788948: 'pythonplays'}, {1231506990: 'kobascalls'}, {1512654466: 'future_lounge_calls'}, {1523868855: 'cryptocatcalls'}, {1711456893: 'emilyscrypto'}, {1766901988: 'lowtaxbsc'}, {1822520617: 'degensgod_callz'}, {1580404073: 'midnightcallss'}, {1736901313: 'gemsofra'}, {1541656652: 'civilianinvestors'}, {1775159867: 'simoncallssafu'}, {1954194476: 'green_apes_gamble'}, {1336011805: 'bomb_crews'}, {1246339685: 'scrooge_calls'}, {1584272816: 'ramjofficialcalls'}, {1706033216: 'royal_callz'}, {1577316060: 'monkeytreasury'}, {1522542784: 'genghishhancalls'}, {1794471884: 'minegems'}, {1939898684: 'thedailymememag'}, {1868938090: 'newdogeneratescalls'}, {1731094822: 'fvkcalls'}, {1967678588: 'gainzogambles'}, {1841136956: 'altrogems'}, {1189365752: 'marcoscalls'}, {1608966492: 'whaleschronicles'}, {1533144110: 'zlaunchbotofficial'}, {1589356016: 'zibscalls'}, {1949113164: 'medfilcalls'}, {1598761859: 'medusacalls'}, {1593755161: 'craftygems'}, {1717572891: 'acidonmeliketheraincalls'}, {1665735419: 'hulksdegens'}, {1808935697: 'kulturecalls'}, {1897782479: 'degenliam'}, {1627794116: 'the_gemsz'}, {1947077968: 'rarbincalledit'}, {1543776876: 'brotherservices'}, {1591702975: 'perrycalls'}, {1819368322: 'houseofdegeneracy'}, {1755965782: 'habibigemcalls'}, {1668861967: 'zizzleshizzle'}, {1972967780: 'crimsonscryptos'}, {1655277888: 'zorincalls'}, {1710455682: 'odglug69'}, {1691007368: 'leopardcalls'}]

chat_id_to_name = {}
for item in TELEGRAM_GROUPS:
    for chat_id, channel_name in item.items():
        chat_id_to_name[chat_id] = channel_name

# Create a list of chat IDs from the dictionary
chat_ids = list(chat_id_to_name.keys())


#Handling the telegram client and queue
# Configuration
MAX_QUEUE_SIZE = 8
SLEEP_DURATION = 2

# Create an asynchronous queue to handle messages
message_queue = Queue(maxsize=MAX_QUEUE_SIZE)

# Initialize the clientTG
clientTG = TelegramClient('callchannels', API_ID, API_HASH)

# Event handler to listen to new messages
@clientTG.on(events.NewMessage(chats=chat_ids))
async def new_message_listener(event):
    try:
        # Try to add the event to the queue
        await message_queue.put(event)
    except asyncio.QueueFull:
        # If the queue is full, reconnect and clear the queue
        await reconnect_client()


async def reconnect_client():
    global message_queue
    await clientTG.disconnect()
    print("telegram client disconnected")
    message_queue = Queue(maxsize=MAX_QUEUE_SIZE)  # Clearing the queue
    await clientTG.connect()
    print("telegram client reconnected")

def match_telegram_with_address(text):
            # step 1: extract the telegram address
            def extract_username(calltext):
                # The regex pattern will look for either '@' or 't.me/' followed by the username.
                # The username is assumed to consist of alphanumeric characters, underscores, or periods.
                pattern = r'@([\w\.]+)|t\.me/([\w\.]+)'
                match = re.search(pattern, calltext, re.IGNORECASE)

                if match:
                    # Return the first non-None group
                    return next(group for group in match.groups() if group)

                return None
            username = extract_username(text)
            print(f"extracted username {username}")
            if not username:
                return []

            #step 2: for each tg in the array search the last 48 hours of tokens within the object social media and telegram for a match
            from datetime import datetime, timedelta

            # Calculate the timestamp for 24 hours ago in UTC
            time_24_hours_ago = datetime.utcnow() - timedelta(days=60)

            # Define the regular expression pattern to match the variations of the Telegram username
            telegram_pattern = rf"(@{username}|t\.me/{username}|https://t\.me/{username})"
            
            query = {
                "social_media.telegram": {"$regex": telegram_pattern, "$options": "i"},  # Case-insensitive regex search
                "events.deployed.timestamp": {"$gt": time_24_hours_ago}  # Check the timestamp of deployed event
            }

            # Fetch documents from MongoDB using the defined query
            documents = db['tokens'].find(query).sort("events.deployed.timestamp", -1)

            # Extract the Ethereum addresses (_id field)
            ethereum_addresses = [doc['_id'] for doc in documents]
            return ethereum_addresses

# Worker to process queued messages
async def message_worker():
    while True:
        # Wait for a message from the queue
        event = await message_queue.get()

        # Handle the message (This should be your current message handling code)
        await handle_message(event)

        # Sleep for the defined duration to avoid hitting rate limits
        await asyncio.sleep(SLEEP_DURATION)

def handle_exception(loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    print(f"Caught exception: {msg}")
    loop.create_task(reconnect_client())


# Handle the message (Your current message handling code)
async def handle_message(event):
    try:
        
        # ... [Your current message processing logic]
        # Extract the text from the message
        message_text = event.message.text
        
        # Extract the token address from the text (using our previous functions)
        token_address = extract_relevant_address_from_text(message_text)
        
        if not token_address:
            token_address = match_telegram_with_address(message_text)
        # If a token address was found, process it (e.g., print it)
        if token_address:
            #translates the telethon chat id into a readable format by our dictionary, removes -100 prefix
            if str(event.chat_id).startswith("-100"):
                actual_chat_id = int(str(event.chat_id)[4:])
            else:
                actual_chat_id = event.chat_id

            print(f"\n ----------------- \n\n **Found token address:** {token_address} in {chat_id_to_name[actual_chat_id]}")
            number_marketcap = None
            number_liquidity = None
            try:
                marketcap, liquidity = ethsourcecode.get_marketcap(token_address)
                number_marketcap = ethsourcecode.smart_parse_number(marketcap)
                number_liquidity = ethsourcecode.smart_parse_number(liquidity)
            except Exception as e:
                pass

        
            #Database work to update the posts in the channels as well as save the data in both collections tokens and channels
            # Now, you can access the message ID using sent_message.id
            message_id = event.id
            timestamp_utc = event.date
            # Define the filter and the update
            
            filter_ = {"_id": {"$regex": f"^{token_address}$", "$options": 'i'}}
            update_ = {
                "$push": {
                    "channels": {
                    "channel_name": f"{chat_id_to_name[actual_chat_id]}",
                    "channel_id": actual_chat_id,
                    "timestamp": timestamp_utc,
                    "marketcap": number_marketcap,
                    "liquidity": number_liquidity,
                    "channel_post": f"{message_text}",
                    "channel_post_url": f"https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}"
                }
                }
            }

            # Use upsert=True to insert if not exists, or update if exists
            tokens.update_one(filter_, update_, upsert=False)

            await asyncio.sleep(2)
            # Fetch token data by contract address
            token_data = database_manager.get_token_data(token_address)
            print(f"\n\nThis is the mongo db token data {token_data}")
            
            # Check if the token data was found
            if token_data is not None:
                
                # Extract event data from the token data document
                deployed_event = token_data.get("events", {}).get("deployed", {})
                verified_event = token_data.get("events", {}).get("verified", {})
                locked_event = token_data.get("events", {}).get("locked", {})
                burned_event = token_data.get("events", {}).get("burned", {})
                called_event = token_data.get("events", {}).get("called", {})
                #extract token call channel events:
                channels_events = token_data.get("channels", None)
                channels_text = ""
                # If channels are present
                if channels_events:
                    # Getting the number of distinct call channels
                    distinct_channels = set(channel['channel_name'] for channel in channels_events)
                    num_distinct_channels = len(distinct_channels)
                    
                    # Getting the total number of calls
                    total_calls = len(channels_events)
                    
                    # Edit the message in the target channel with new content
                    channels_text = f"\n[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)\n[🔊](emoji/5823192186916704073)**Called **`{total_calls} times`  **by** `{num_distinct_channels} Channels`**:** \n[🔽](emoji/5820990556616004290)\n"
                    print(f"Called by {num_distinct_channels} call channels")
                    print(f"Total number of calls: {total_calls}")
                    
                    # Listing each channel with timestamp and marketcap
                    for channel in channels_events:
                        channel_name = channel.get('channel_name')
                        channel_url = channel.get('channel_post_url')
                        

                        if total_calls < 11:
                            timestamp = channel.get('timestamp')
                            channel_marketcap = channel.get('marketcap')
                            print(f'\n\n channel mcap: [💲](emoji/5816854146627671089){channel_marketcap} \n\n')
                            #edge case in case mcarketcap is empty
                            if channel_marketcap is None:
                                channels_text += f"  [▶️](emoji/5816812219156927426) [@{channel_name}]({channel_url})  [▶️](emoji/5827885422235095225)  __{timestamp}__\n "
                            else:
                                smart_mc =ethsourcecode.smart_format_number(channel_marketcap)
                                channels_text += f"  [▶️](emoji/5816812219156927426) [@{channel_name}]({channel_url})  [▶️](emoji/5827885422235095225)  [💲](emoji/5816854146627671089)**Mc: {smart_mc}**  [▶️](emoji/5827885422235095225)  __{timestamp}__\n "

                            print(f"\nChannel Name: {channel_name}")
                            print(f"Timestamp: {timestamp}")
                        else:
                            
                            channel_marketcap = channel.get('marketcap')
                            print(f'\n\n channel mcap: [💲](emoji/5816854146627671089){channel_marketcap} \n\n')
                            #edge case in case mcarketcap is empty
                            if channel_marketcap is None:
                                channels_text += f" [@{channel_name}]({channel_url}), "
                            else:
                                smart_mc =ethsourcecode.smart_format_number(channel_marketcap)
                                channels_text += f" [@{channel_name}]({channel_url}) {smart_mc}, "
                

                #add the call event and post in the calls list telegram group or update if there is already a post


                # Extract message_id and message_text from each event data
                deployed_message_id = deployed_event.get("message_id", None)
                deployed_message = deployed_event.get("message_text", None)
                verified_message_id = verified_event.get("message_id", None)
                verified_message = verified_event.get("message_text", None)
                lock_message_id = locked_event.get("message_id", None)
                lock_message = locked_event.get("message_text", None)
                burn_message_id = burned_event.get("message_id", None)
                burn_message = burned_event.get("message_text", None)
                #call list data if available
                call_message_id = called_event.get("message_id", None)
                call_message = called_event.get("message_text", None)

                #simple function to conditionally post text depending on if the token has an mc or not
                def marketcap_text(mc):
                    if marketcap is None:
                        return ""
                    else:
                        return f"at [💲](emoji/5816854146627671089)**{mc} MC**"
                    
                #Parallel calls for both edits and replies to satisfy telethon api rate limits
                # List to hold the tasks
                edit_tasks = []
                send_tasks = []
                
                #After finishing the analysis we edit the already posted messages with the contract address as a key
                if deployed_message_id is not None:
                    
                        # Edit the message in the target channel with new content
                        new_text = deployed_message + channels_text
                        #f"\n---------------------------------\n**[🔊](emoji/5823192186916704073)Called By:**\n [🔽](emoji/5820990556616004290)\n**  ⟹{chat_id_to_name[actual_chat_id]}** at {timestamp_utc} "
                        print("deployed message edit...")
                        edit_tasks.append(clientTG.edit_message(target_deployed, deployed_message_id, new_text, parse_mode=CustomMarkdown(), link_preview=False))

                        #reply to the message as well to make the call visible
                        response_text = f" \n [🔊](emoji/5823192186916704073)**Call Alert:**\n [▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609) \n `{chat_id_to_name[actual_chat_id]}` just called {marketcap_text(marketcap)}\n https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}  "
                        #time.sleep(0.2)
                        print("deployed message reply...")
                        #send_tasks.append(clientTG.send_message(target_deployed, response_text, reply_to=deployed_message_id,parse_mode=CustomMarkdown(), link_preview=False ))

                if verified_message_id is not None:
                    
                        # Edit the message in the target channel with new content
                        new_text = verified_message + channels_text
                        edit_tasks.append(clientTG.edit_message(target_verified, verified_message_id, new_text, parse_mode=CustomMarkdown(), link_preview=False))
                        #reply to the message as well to make the call visible
                        
                        #response_text = f" \n [🔊](emoji/5823192186916704073)**Call Alert:**\n [▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609) \n `{chat_id_to_name[actual_chat_id]}` just called {marketcap_text(marketcap)}\n https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}  "
                        #time.sleep(0.2)
                        #send_tasks.append(clientTG.send_message(target_verified, response_text, reply_to=verified_message_id,link_preview=False, parse_mode=CustomMarkdown()))

                if lock_message_id is not None:
                    
                        # Edit the message in the target channel with new content
                        new_text = lock_message + channels_text
                        edit_tasks.append(clientTG.edit_message(target_longlock, lock_message_id, new_text, parse_mode=CustomMarkdown(), link_preview=False))
                        #reply to the message as well to make the call visible
                        
                        #response_text = f" \n [🔊](emoji/5823192186916704073)**Call Alert:**\n [▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609) \n `{chat_id_to_name[actual_chat_id]}` just called {marketcap_text(marketcap)}\n https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}  "
                        #time.sleep(0.2)
                        #send_tasks.append(clientTG.send_message(target_longlock, response_text, reply_to=lock_message_id, link_preview=False, parse_mode=CustomMarkdown()))

                if burn_message_id is not None:
                    
                        # Edit the message in the target channel with new content
                        new_text = burn_message + channels_text
                        edit_tasks.append(clientTG.edit_message(target_burn, burn_message_id, new_text, parse_mode=CustomMarkdown(), link_preview=False))
                        #reply to the message as well to make the call visible
                        
                        #response_text = f" \n [🔊](emoji/5823192186916704073)**Call Alert:**\n [▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609) \n `{chat_id_to_name[actual_chat_id]}` just called {marketcap_text(marketcap)}\n https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}  "
                        #time.sleep(0.2)
                        #send_tasks.append(clientTG.send_message(target_burn, response_text, reply_to=burn_message_id, link_preview=False, parse_mode=CustomMarkdown()))

                ############################################################
                ####### #Manages the ************* CALL LIST CHANNEL ************* and all its fucking edge cases
                if call_message_id is not None:
                    
                        # Edit the message in the target channel with new content
                        new_text = call_message + channels_text
                        edit_tasks.append(clientTG.edit_message(target_call, call_message_id, new_text, parse_mode=CustomMarkdown(), link_preview=False))
                        
                        #reply for a call notification
                        response_text = f" \n [🔊](emoji/5823192186916704073)**Call Alert:**\n [▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609)[▶️](emoji/5814397073147039609) \n `{chat_id_to_name[actual_chat_id]}` just called {marketcap_text(marketcap)}\n https://t.me/{chat_id_to_name[actual_chat_id]}/{message_id}  "
                        send_tasks.append(clientTG.send_message(target_call, response_text, reply_to=call_message_id, link_preview=False, parse_mode=CustomMarkdown()))
                        
                     
                if call_message_id is None:
                    #in case this is the first call we need to form the latest message available to send as text + the first call data
                    call_text = ""

                    if burn_message_id is not None:
                        call_text = burn_message + channels_text
                        
                        sentcall_message = await clientTG.send_message(target_call, call_text, link_preview=False, parse_mode=CustomMarkdown())
                        call_message_id = sentcall_message.id
                        call_timestamp_utc = sentcall_message.date
                        
                        # Define the filter and the update
                        
                        filter_ = {"_id": {"$regex": f"^{token_address}$", "$options": 'i'}}
                        update_ = {
                            "$set": {
                                "events.called": {
                                    "timestamp": call_timestamp_utc,
                                    "message_id": call_message_id,
                                    "message_text": burn_message,
                                    "caller_username": channel_name ,
                                    #"called_telegram_id": actual_chat_id,
                                    "call_url": channel_url ,
                                    "earliest_marketcap": number_marketcap
                                },

                            }
                        }

                        # Use upsert=True to insert if not exists, or update if exists
                        tokens.update_one(filter_, update_, upsert=True)

                    elif lock_message_id is not None:
                        call_text = lock_message + channels_text
                        
                        sentcall_message = await clientTG.send_message(target_call, call_text, link_preview=False, parse_mode=CustomMarkdown())
                        call_message_id = sentcall_message.id
                        call_timestamp_utc = sentcall_message.date
                        
                        # Define the filter and the update
                        
                        filter_ = {"_id": {"$regex": f"^{token_address}$", "$options": 'i'}}
                        update_ = {
                            "$set": {
                                "events.called": {
                                    "timestamp": call_timestamp_utc,
                                    "message_id": call_message_id,
                                    "message_text": lock_message,
                                    "caller_username": channel_name ,
                                    #"called_telegram_id": actual_chat_id,
                                    "call_url": channel_url ,
                                    "earliest_marketcap": number_marketcap
                                },

                            }
                        }

                        # Use upsert=True to insert if not exists, or update if exists
                        tokens.update_one(filter_, update_, upsert=True)

                    elif verified_message_id is not None:
                        call_text = verified_message + channels_text
                        
                        sentcall_message = await clientTG.send_message(target_call, call_text, link_preview=False, parse_mode=CustomMarkdown())
                        call_message_id = sentcall_message.id
                        call_timestamp_utc = sentcall_message.date
                        
                        # Define the filter and the update
                        
                        filter_ = {"_id": {"$regex": f"^{token_address}$", "$options": 'i'}}
                        update_ = {
                            "$set": {
                                "events.called": {
                                    "timestamp": call_timestamp_utc,
                                    "message_id": call_message_id,
                                    "message_text": verified_message,
                                    "caller_username": channel_name ,
                                    #"called_telegram_id": actual_chat_id,
                                    "call_url": channel_url ,
                                    "earliest_marketcap": number_marketcap
                                },

                            }
                        }

                        # Use upsert=True to insert if not exists, or update if exists
                        tokens.update_one(filter_, update_, upsert=True)

                    elif deployed_message_id is not None:
                        call_text = deployed_message + channels_text
                    
                        sentcall_message = await clientTG.send_message(target_call, call_text, link_preview=False, parse_mode=CustomMarkdown())
                        call_message_id = sentcall_message.id
                        call_timestamp_utc = sentcall_message.date
                        
                        # Define the filter and the update
                        
                        filter_ = {"_id": {"$regex": f"^{token_address}$", "$options": 'i'}}
                        update_ = {
                            "$set": {
                                "events.called": {
                                    "timestamp": call_timestamp_utc,
                                    "message_id": call_message_id,
                                    "message_text": deployed_message,
                                    "caller_username": channel_name ,
                                    #"called_telegram_id": actual_chat_id,
                                    "call_url": channel_url ,
                                    "earliest_marketcap": number_marketcap
                                },

                            }
                        }

                        # Use upsert=True to insert if not exists, or update if exists
                        tokens.update_one(filter_, update_, upsert=True)
                        

                        


                # wait for all the edit_message tasks to complete
                await asyncio.gather(*edit_tasks)
                
                # wait for all the send_message tasks to complete
                await asyncio.gather(*send_tasks)

    except InvalidBufferError as e:
        print(f"Rate-limited. error occurred {e}")
        await asyncio.sleep(9)
        await reconnect_client()  # Explicitly calling the reconnect function here
    except Exception as e:
        print(f"Error occurred: {e}")
        await asyncio.sleep(7)                



async def main():
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(handle_exception)

        await clientTG.start()
        clientTG.parse_mode = CustomMarkdown()
        d = await clientTG.get_input_entity("https://t.me/+k6XPgoum2QQ1ZWU8") #deployed
        print(d)
        t = await clientTG.get_input_entity("https://t.me/+8WG0VhMxLOFmY2Rk") #burned
        print(t)
        v = await clientTG.get_input_entity("https://t.me/+Jtx2Y2xV1VFhYWZk") #verified
        print(v)
        l = await clientTG.get_input_entity("https://t.me/+Ms9zqVwjRVowMzU0") #longlock
        print(l)
        c = await clientTG.get_input_entity("https://t.me/EOTgroupedcalls") #longlock
        print(c)
        #Start the message worker
        task = asyncio.create_task(message_worker())
        await task  # Ensure the task is awaited
        logger.info("Bot is running...")
        await clientTG.run_until_disconnected()
    except Exception as e:
        print(f"Global Exception: {e}")
        await reconnect_client()  


if __name__ == '__main__':
    asyncio.run(main())






s
