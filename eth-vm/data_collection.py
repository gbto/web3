import json
import logging
import os
import time

import pandas as pd
import requests
import yaml
from eth_utils import event_abi_to_log_topic
from hexbytes import HexBytes
from tqdm import tqdm
from web3 import Web3
from web3._utils.events import get_event_data
from web3.middleware.geth_poa import geth_poa_middleware

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger.setLevel(logging.INFO)


class Web3ToolKit:
    """Set of utils to collect data via web3.

    This classes contains methods for pulling data from ethereum compatible networks. It can
    be used for the BSC chain, Polygon or Ethereum, for which we need to provide a pair of URL and KEY
    for both the block explorer API (etherscan, polygonscan, bscscan) or and the node to which to
    connect via web3."""

    def __init__(self, network: str):

        self.network = network

        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)
        self.api_url = self.config.get(self.network)["API_URL"]
        self.node_url = self.config.get(self.network)["NODE_URL"]
        self.api_key = os.environ.get(f"{self.network.upper()}_API_KEY")
        self.node_key = os.environ.get(f"ALCHEMY_{self.network.upper()}_NODE_KEY")

        self.w3 = self.connect_web3()
        self.start_block, self.end_block = 1, self.w3.eth.blockNumber

    def connect_web3(self):
        """Connect to the network with w3 and returns the client and latest block."""

        # Create connection
        url = f"{self.node_url}{self.node_key}/"
        w3 = Web3(Web3.HTTPProvider(url))
        if self.network == "polygon":
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Verify connection
        if w3.isConnected():
            try:
                block = w3.eth.blockNumber
                logger.info(f"Successfully connected to {self.network} network through web3. Block #{block}")
                return w3
            except Exception as e:
                return e
        else:
            ConnectionError("Couldn't connect successfully through web3.")

        return w3

    def search_contract_implementation_address(self, address: str) -> str:
        """Retrieve the implementation address of a conrtract.

        Try to collect the implementation address of the contract if it is implemented behind a proxy address.

        Args:
            address (str): The contract address.

        Returns:
            str: The address of the actual contract implementation.
        """

        try:
            # get contract implementation address from proxy contract address. The storage_slot is a default values
            # more explanation can be found at https://eips.ethereum.org/EIPS/eip-1967#logic-contract-address
            storage_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
            impl_address = self.w3.eth.getStorageAt(Web3.toChecksumAddress(address), position=storage_slot)
            impl_address = Web3.toHex(impl_address).replace("000000000000000000000000", "")

        except Exception as e:
            impl_address = None
            logger.error(f"Failed retrieving data from implementation storage slot. ERROR: {e}")

        return impl_address

    def request_contract_abi(self, address: str, max_trials: int = 10) -> dict:
        """Extract from an explorer's API the ABI of a given smart contract.

        Args:
            address (str): The address
            max_trials (int, optional): Maximum number of trials. Defaults to 10.

        Raises:
            InterruptedError: The requests didn't succeed before the max_trials values has been reached.
            Exception: The requests didn't succeed for another reason than connection issue.

        Returns:
            dict: The JSON formatted ABI of the smart contract.
        """

        try:
            request_params = dict(
                address=address,
                module="contract",
                action="getabi",
                apikey=self.api_key,
            )
            response = requests.post(self.api_url, params=request_params).json()

            if response.get("status") == "1":
                abi = json.loads(response.get("result"))

            elif response.get("status") == "0":
                abi = None
                error_message = f"There's been an issue while retrieving the contract ABI ({address}). " f"ERROR: {response.get('result')}"
                logger.error(error_message)

            else:
                abi = None
                error_message = f"There's been an unknown issue while retrieving the contract's ABI ({address})."
                logger.error(error_message)

        except Exception as e:
            logger.info(f"The call to the ABI didn't work. ERROR: {e}")

        return abi

    def create_contract_abi_events(self, abi: dict) -> dict:
        """Get the keccak hash of the events of a smart contract ABI.

        The keccak hash of a contract abi event can be used to filter API call logs by topic.
        By passing a keccak hash to the topic parameter we only will retrieve the logs of a specific event.

        Args:
            abi (dict): The ABI of the smart contract, as dictionary.

        Returns:
            dict: A dictionary having the event hash as keys the corresponding ABI event as values.
        """

        contract_events = [field for field in abi if field["type"] == "event"]
        contract_events_hash = {event_abi_to_log_topic(abi_event): abi_event for abi_event in contract_events}

        return contract_events_hash

    def create_contract_instance(self, address: str, max_trials: int = 2):
        """Get contract ABI and creates the web3 contract instance for decoding transactions inputs.

        Args:
            address (str): The address of the contract we want to instantiate.
            max_trials (int, optional): Maximum number of trials. Defaults to 10.

        Raises:
            InterruptedError: The requests didn't succeed before the max_trials values has been reached.

        Returns:
            Web3.Contract: The instance of the smart contract used for decoding inputs.
        """

        address = Web3.toChecksumAddress(address)
        contract_instance = None
        n_trials = 0

        while contract_instance is None:

            if n_trials > max_trials:
                raise InterruptedError("Couldn't retrieve the ABI after {n_trials} trials. Operation canceled.")

            try:
                contract_abi = self.request_contract_abi(address=address)
                contract_instance = self.w3.eth.contract(address=address, abi=contract_abi)
                n_trials += 1

            except Exception as e:
                raise Exception(f"The call to the ABI didn't work. ERROR: {e}")

        return contract_instance


class ContractTransactions(Web3ToolKit):
    """Collects and decodes transactions.

    This class inherits from all the Web3ToolKit methods and variables. It is designed to collect and decode
    transactions initiated by users to a given smart contract.
    """

    def __init__(self, network):

        super().__init__(network)
        self.pagination_offset = 10_000

    def request_contract_transactions(self, address: str, start_block: int, end_block: int) -> dict:
        """Extract all the transactions between 2 blocks for a given contract.

        Args:
            address (str): The contract address.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            dict(any): All the base currencies transactions of the wallet between 2 blocks.
        """

        data = list()
        request_params = dict()
        request_params["startblock"] = start_block
        request_params["endblock"] = end_block
        request_params["address"] = address
        request_params["apikey"] = self.api_key
        request_params["module"] = "account"
        request_params["action"] = "txlist"

        while True:

            # Collect the data
            _s, _e = request_params.get("startblock"), request_params.get("endblock")
            logger.info(f"Extracting transactions from {_s} to {_e} for contract {address}")

            response = requests.post(self.api_url, params=request_params)
            response = response.json().get("result")
            data.append(response)

            if not response:
                logger.info("No data to return for the specified block span.")
                break

            else:
                try:
                    # Handle the exit of the while loop
                    resp_block = max(int(x.get("blockNumber")) for x in response)
                    resp_count = len(response)
                    if resp_block < request_params.get("endblock") and resp_count == self.pagination_offset:
                        request_params["startblock"] = resp_block
                        continue
                    else:
                        logger.info("Finished downloading all the requested transactions.")
                        break

                except Exception as e:
                    logger.error(f"Failed request with ERROR: {e}. Trying again.")
                    time.sleep(5)
                    pass

        data = [tx for batch in data for tx in batch] if len(data) > 1 else data[0]
        return data

    def decode_contract_transactions_input(self, contract_transactions: list[dict], contract_instance):
        """Decode the input of transactions executed by a contract.

        Args:
            contract_transactions (list(dict)): The list of transactions with raw inputs.
            contract_instance (web3.Contract)): The web3 instance of the contract.
        Returns:
            list(dict): The list of transactions with decoded inputs.
        """

        # decode the contract transactions logs
        for transaction in tqdm(contract_transactions):

            try:
                transaction_input = contract_instance.decode_function_input(str(transaction.get("input")))
                transaction["function_called"] = transaction_input[0].fn_name
                transaction["function_parameters"] = transaction_input[1]
            except ValueError:
                transaction_input = tuple([None, dict()])

        return contract_transactions

    def format_contract_transactions_input(self, contract_transactions: list[dict]):
        """Format the resulting dataset by replacing hexadecimal values by human readable format."""

        df = pd.DataFrame(contract_transactions)
        df["timeStamp"] = pd.to_datetime(df["timeStamp"], unit="s")

        # numerics
        integers = [
            "blockNumber",
            "nonce",
            "value",
            "gas",
            "gasPrice",
            "gasUsed",
            "cumulativeGasUsed",
            "confirmations",
            "transactionIndex",
            "txreceipt_status",
            "isError",
        ]

        for f in integers:
            df[f] = df[f].astype(str)
            df[f] = df[f].apply(int, base=16)
        return df

    def fetch_contract_transactions(self, address, start_block: int, end_block: int):
        """Extract and decode the transactions of a given smart contract over a specified block span.

        The process is to first look whether the contract is implemented at another address, then retrieve
        all transactions from the block explorer API, create a web3 contract instance that we can then use
        to decode the input of the retrieved transactions.

        Args:
            address (str): The contract address to query.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            dict: The contract transactions between 2 blocks, with decoded input.
        """

        contract_impl_address = self.search_contract_implementation_address(address)

        try:
            if not contract_impl_address or contract_impl_address == "0x0000000000000000":
                # The contract is not behind any proxy address
                contract_transactions = self.request_contract_transactions(address, start_block, end_block)
                contract_instance = self.create_contract_instance(address)

            else:
                # The contract implementation is behind a proxy address
                contract_proxy_address = Web3.toChecksumAddress(address)
                contract_transactions = self.request_contract_transactions(contract_proxy_address, start_block, end_block)
                contract_instance = self.create_contract_instance(address=contract_impl_address)

            contract_transactions = self.decode_contract_transactions_input(contract_transactions, contract_instance)
            contract_transactions = self.format_contract_transactions_input(contract_transactions)

        except Exception:
            contract_transactions = None

        return contract_transactions


class ContractEventLogs(Web3ToolKit):
    """This class inherits from all the Web3ToolKit methods and variables, and is designed to collect and decode
    the events logs that have been triggered for a given contract.
    """

    def __init__(self, network: str):

        super().__init__(network)
        self.pagination_offset = 1_000

    def request_contract_logs(self, address: str, start_block: int, end_block: int) -> list:
        """Extract all the logs between 2 blocks for a given contract.

        Args:
            address (str): The contract address.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            list(dict): All the logs generated by the smart contract between 2 blocks.
        """

        data = list()
        request_params = dict()
        request_params["fromBlock"] = start_block
        request_params["toBlock"] = end_block
        request_params["address"] = address
        request_params["apikey"] = self.api_key
        request_params["module"] = "logs"
        request_params["action"] = "getLogs"
        request_params["offset"] = self.pagination_offset

        while True:

            # Collect the data
            _s, _e = request_params.get("fromBlock"), request_params.get("toBlock")
            logger.info(f"Extracting logs from {_s} to {_e} for contract {address}")

            response = requests.post(self.api_url, params=request_params)
            response = response.json().get("result")
            data.append(response)

            if not response:
                logger.info("No data to return for the specified block span.")
                break
            else:
                try:
                    # Handle the exit of the while loop
                    resp_block = max(int(x.get("blockNumber"), 16) for x in response)
                    resp_count = len(response)
                    if resp_block < request_params.get("toBlock") and resp_count == self.pagination_offset:
                        request_params["fromBlock"] = resp_block
                        continue
                    else:
                        logger.info("Finished downloading all the requested event logs.")
                        break

                except Exception as e:
                    logger.error(f"Failed request with ERROR: {e}. Trying again.")
                    time.sleep(3)
                    pass

        data = [tx for batch in data for tx in batch] if len(data) > 1 else data[0]
        return data

    def decode_contract_logs_data(self, contract_logs: list[dict], contract_abi_events: dict):
        """Decodes a list of contract logs by using the events ABI extracted from contract ABI. We
        iterate over all the topics of each event log to create a list of decoded log data payload
        which provides all the information about function executed context.

        Args:
            contract_logs (dict): The contract logs with their associated decoded data
            contract_abi_events (dict): The contract events extracted from the contract's ABI.
        """
        for event in tqdm(contract_logs):

            event["topics"] = [HexBytes(topic) for topic in event["topics"]]
            event["blockHash"] = event.get("blockHash")  # mandatory because accessed in web3 utils
            decoded_data = list()

            for topic in event["topics"]:

                # we match event keccak hash and topics to find the events
                event_abi = contract_abi_events.get(topic)

                if event_abi:
                    # if there's a correspondance between event
                    event_data = get_event_data(self.w3.codec, event_abi, event)
                    event_data = dict(event_data.get("args"))
                    event_data["name"] = event_abi.get("name")
                    decoded_data.append(event_data)

                else:
                    # if there's no match, we have to assume there's no logs to decode
                    event_data = list(dict())
                    decoded_data.append(event_data)

            event["decoded_data"] = decoded_data

        return contract_logs

    def format_contract_logs_data(self, contract_logs: list) -> pd.DataFrame:
        """Format the resulting dataset by replacing hexadecimal values by human readable format."""

        df = pd.DataFrame(contract_logs)

        # numerics
        integers = [
            "blockNumber",
            "gasPrice",
            "gasUsed",
            "timeStamp",
            "logIndex",
            "transactionIndex",
        ]

        for f in integers:
            try:
                df[f] = df[f].astype(str)
                df[f] = df[f].apply(int, base=16)
            except ValueError:
                pass

        # timestamps
        df["timeStamp"] = pd.to_datetime(df["timeStamp"], unit="s")

        return df

    def fetch_contract_logs(self, address, start_block: int, end_block: int) -> pd.DataFrame:
        """Extract and decode the logs of a given smart contract over a specified block span.
        The process is to first obtain the contract ABI, extract the events from the contract ABI,
        then retrieve all the contract logs from the block explorer API, and finally create a web3
        contract instance that we can then use to decode the input of the retrieved transactions.

        Args:
            address (str): The contract address to query.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            dict: The contract logs between 2 blocks, with their decoded data.
        """
        contract_impl_address = self.search_contract_implementation_address(address)

        try:
            if not contract_impl_address or contract_impl_address == "0x0000000000000000":
                contract_abi = self.request_contract_abi(address)
                contract_abi_events = self.create_contract_abi_events(contract_abi)
                contract_logs = self.request_contract_logs(address, start_block, end_block)

            else:
                contract_abi = self.request_contract_abi(contract_impl_address)
                contract_abi_events = self.create_contract_abi_events(contract_abi)
                contract_logs = self.request_contract_logs(address, start_block, end_block)

            contract_logs = self.decode_contract_logs_data(contract_logs, contract_abi_events)
            contract_logs = self.format_contract_logs_data(contract_logs)

        except Exception as e:
            contract_logs = None
            error_message = f"Failed retrieving contracts logs because of ERROR: {e}"
            logger.info(error_message)

        return contract_logs


if __name__ == "__main__":

    network = "polygon"
    address = "0xA0eC9E1542485700110688b3e6FbebBDf23cd901"

    start_block = 1
    end_block = 26732552

    txs = ContractTransactions(network).fetch_contract_transactions(address, start_block, end_block)
    log = ContractEventLogs(network).fetch_contract_logs(address, start_block, end_block)
