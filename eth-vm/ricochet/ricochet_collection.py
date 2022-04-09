import logging
import os
import sys

import pandas as pd
import yaml

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from data_collection import ContractEventLogs, ContractTransactions

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Ricochet:
    """Contains the method to the transactions and event logs of Ricochet smart contracts. This class re-uses the module
    developed to fetch and decode ethereum compatible networks' smart contracts transactions and event logs.
    """

    def __init__(self, network: str):
        """Initialize the attributes of the Ricochet class

        Args:
            network (str): The network to connect to (polygon, binance, ethereum, celo...)
        """

        self.network = network
        self.redshift_schema = "ricochet"

        self.start_block = 1
        self.end_block = 26582304

        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)
        self.contracts = self.config.get("contracts")

    def get_transactions(self, address: str, start_block: int, end_block: int):
        """Retrieves all the logs of the events triggered by the smart contract transactions.

        Args:
            address (str):  The contract address.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            pd.DataFrame: The detailed logs with their related decoded data.
        """

        client = ContractTransactions(self.network)

        table_name = "transactions"
        field_name = "blocknumber"

        start_block = start_block if start_block else self.get_cursor(table_name, field_name)
        end_block = end_block if end_block else client.end_block

        data = client.fetch_contract_transactions(address, start_block, end_block)

        return data

    def get_events_logs(self, address: str, start_block: int, end_block: int):
        """Retrieves all the logs of the events triggered by the smart contract transactions.

        Args:
            address (str):  The contract address.
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.

        Returns:
            pd.DataFrame: The detailed logs with their related decoded data.
        """

        client = ContractEventLogs(self.network)

        table_name = "events_logs"
        field_name = "blocknumber"

        start_block = start_block if start_block else self.get_cursor(table_name, field_name)
        end_block = end_block if end_block else client.end_block

        data = client.fetch_contract_logs(address, start_block, end_block)

        return data

    def aggregate_contracts_data(self, start_block: int, end_block: int, category: str = "bank") -> pd.DataFrame:
        """Iterates over the Ricochet contracts listed in the config file in order to extract and decode for each
        the transactions and event logs that occurred between 2 blocks.

        Args:
            start_block (int): The starting block of the extraction.
            end_block (int): The upper limit block of the extraction.
            category (str): The category of contracts to fetch data. Defaults to 'bank'.

        Returns:
            pd.DataFrame: The aggregated transactions and event logs for a list of contracts.
        """

        contracts_logs = pd.DataFrame()
        contracts_txs = pd.DataFrame()

        for contract in self.contracts.get(category):

            result = None
            while result is None:
                # TODO: Maybe adding the contract address or category to the tables
                try:
                    logger.info(f"Collect the {contract} transactions")
                    txs = self.get_transactions(contract, start_block, end_block)
                    contracts_txs = contracts_txs.append(txs)

                    logger.info(f"Collect the {contract} event logs")
                    logs = self.get_events_logs(contract, start_block, end_block)
                    contracts_logs = contracts_logs.append(logs)

                    # exit the while loop
                    result = True

                except Exception as e:
                    print(f"ERROR {e}")
                    continue

        return (contracts_txs, contracts_logs)


if __name__ == "__main__":

    client = Ricochet("polygon")

    start_block = 1
    end_block = 26582304

    # Collect all logs and transactions for a specific contract
    # address = '0xA0eC9E1542485700110688b3e6FbebBDf23cd901'
    # txs = client.get_transactions(address, start_block, end_block)
    # logs = client.get_events_logs(address, start_block, end_block)

    # Collect all logs and transactions for a contract category
    contract_category = "bank"
    txs, logs = client.aggregate_contracts_data(start_block, end_block, contract_category)
