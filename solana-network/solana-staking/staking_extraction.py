import datetime
import os

import numpy as np
import pandas as pd
import requests
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import MemcmpOpts
from tqdm import tqdm


class SolanaAPI:
    """This class contains methods that extracts data related to the solana blockchain.

    We use both the RPC API https://docs.solana.com/developing/clients/jsonrpc-api and
    solanascan API where some data is already indexed.
    """

    def __init__(self):

        self.figment_api_key = os.environ["FIGMENT_DATAHUB_API_KEY"]
        self.figment_api_url = "https://solana--mainnet.datahub.figment.io/"
        self.api = Client(self.figment_api_url + f"apikey/{self.figment_api_key}/")
        self.headers = {
            "Authorization": self.figment_api_key,
            "Content-Type": "application/json",
        }

        self.solscan_url = "https://public-api.solscan.io/"
        self.solscan_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}

        self.execution_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.start_date = datetime.datetime(2020, 1, 1)
        self.end_date = self.execution_timestamp

        self.start_epoch = 0
        current_epoch_info = self.api.get_epoch_info().get("result")
        self.current_epoch = current_epoch_info.get("epoch")
        self.slot = current_epoch_info.get("absoluteSlot")

        self.wallet_address = "LDwVxy6FopzHHSDLvgKaDEV7gtk6VaoNWEn461hzAbi"
        self.validator_node_key = "q9XWcZ7T1wP4bW9SB4XgNNwjnFEJ982nE8aVbbNuwot"
        self.validator_vote_key = "26pV97Ce83ZQ6Kz9XT4td8tdoUFPTng8Fb8gPyc53dJx"

    def get_current_epoch_info(self):
        """Extract information about the current epoch."""
        info = self.api.get_epoch_info().get("result")
        inflation = self.api.get_inflation_rate().get("result")
        data = pd.merge(
            pd.DataFrame.from_dict(info, orient="index").T,
            pd.DataFrame.from_dict(inflation, orient="index").T,
            on="epoch",
        )
        return data

    def get_token_list(self) -> pd.DataFrame:
        """Extract the list of all tokens existing on Solana through solanascan API."""

        token_list = list()
        url = self.solscan_url + "token/list?"
        headers = self.solscan_headers
        limit = 5000
        offset = 1

        while True:
            response = requests.get(
                url,
                headers=headers,
                params=dict(
                    limit=limit,
                    sortBy="market_cap",
                    direction="desc",
                    offset=offset,
                ),
            ).json()
            data = pd.DataFrame(response.get("data"))
            token_list.append(data)
            offset = offset + limit
            if data.shape[0] < limit:
                break

        token_list = pd.concat(token_list).reset_index(drop=True)
        return token_list

    def get_transaction_information(self, transaction_hash: str):
        """Extract detailed information about a specific transaction from Solana RPC API."""

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [transaction_hash, "json"],
        }
        response = requests.post(
            url="https://api.mainnet-beta.solana.com",
            headers=self.headers,
            json=payload,
        ).json()

        data = pd.DataFrame.from_dict(response.get("result"), orient="index").T
        return data

    def get_all_transactions(self, start_date: datetime.datetime, address: str = None, limit=50):
        """Extract all the transactions for an account from solanascan API."""

        address = self.wallet_address if not address else address
        before_hash = None
        txs_list = list()

        url = self.solscan_url + "account/transactions?"
        headers = self.solscan_headers

        while True:
            response = requests.get(
                url,
                headers=headers,
                params=dict(limit=limit, account=address, beforeHash=before_hash),
            ).json()
            txs_list.append(pd.DataFrame(response))

            if len(response) == 0:
                print(f"No transactions returned for address {address} " f"between {self.start_date} and {self.end_date}")
                break

            elif type(response) == dict:
                print(response.get("error").get("message"))
                break

            else:
                last_transaction = response[-1]
                before_hash = last_transaction.get("txHash")
                block_time = datetime.datetime.fromtimestamp(last_transaction.get("blockTime"))
                if len(response) < limit or block_time < start_date:
                    break

        try:
            data = pd.concat(txs_list)
            data["wallet_address"] = address
            data["inserted_at"] = self.execution_timestamp
            data["blockTime"] = pd.to_datetime(data["blockTime"], unit="s")
            data["functions_called"] = [[x.get("type") for x in d] for d in data["parsedInstruction"]]
            data = data[data["blockTime"] > start_date]

        except Exception:
            print("No transactions returned.")
            data = pd.DataFrame()

        return data

    def get_solana_transfers(self, start_date: datetime.datetime, address: str = None, limit=100):
        """Extract solana transfers from all transactions of a given account.

        Are filtered out the programs related transactions as well as the token transfers.
        """

        address = self.wallet_address if not address else address
        transactions = self.get_all_transactions(address=address, start_date=start_date)
        sol_transfers = transactions.explode("functions_called").query('functions_called == "sol-transfer"')

        if len(sol_transfers) > 0:

            data = pd.DataFrame()
            for hash in sol_transfers["txHash"]:
                tx_info = self.get_transaction_information(hash)
                data = data.append(tx_info)

            data = pd.concat(
                [
                    data.reset_index(drop=True).drop(["meta", "transaction"], axis=1),
                    pd.json_normalize(data["meta"]).reset_index(drop=True),
                    pd.json_normalize(data["transaction"]).reset_index(drop=True),
                ],
                axis=1,
            )

            data["wallet_address"] = address
            data["inserted_at"] = self.execution_timestamp
            data["blockTime"] = pd.to_datetime(data["blockTime"], unit="s")

        else:

            print(f"No transactions returned for that time span: {start_date} - {self.end_date}")
            data = pd.DataFrame()

        return data

    def get_cluster_nodes(self):
        """Extract the list of all cluster nodes at the execution date."""

        data = pd.DataFrame(self.api.get_cluster_nodes().get("result"))
        data["inserted_at"] = datetime.datetime.now()
        return data

    def get_validators_snapshot(self):
        """Extract the current and delinquent validators list."""

        validators = self.api.get_vote_accounts().get("result")

        delinquent = pd.DataFrame(validators.get("delinquent"))
        delinquent["status"] = "delinquent"
        current = pd.DataFrame(validators.get("current"))
        current["status"] = "current"

        validators = pd.concat([delinquent, current]).reset_index(drop=True)
        validators["inserted_at"] = datetime.datetime.now()

        return validators

    def get_validators_rewards(self, vote_keys: list = None, start_epoch: int = None):
        """Extract the inflation reward for validators."""

        if not vote_keys:
            vote_keys = self.get_validators_snapshot()["votePubkey"].tolist()

        if not start_epoch:
            start_epoch = self.get_start_epoch("solana_validators_rewards", "epoch")

        data = list()
        chunk_size = 100
        vote_keys_chunks = [vote_keys[i : i + chunk_size] for i in range(0, len(vote_keys), chunk_size)]

        for epoch in tqdm(range(start_epoch, self.current_epoch)):
            # pull data for the next epoch of what's in the db, until the previous epoch from current
            for chunk in vote_keys_chunks:

                url = self.figment_api_url
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getInflationReward",
                    "params": [chunk, {"epoch": epoch}],
                }
                response = requests.post(url, headers=self.headers, json=payload).json().get("result")

                if not response:
                    df = pd.DataFrame()
                else:
                    response = [x if x is not None else dict() for x in response]
                    df = pd.DataFrame(response)
                    df["votePubkey"] = chunk
                    df["epoch"] = epoch
                    df["inserted_at"] = self.execution_timestamp

                data.append(df)

        try:
            data = pd.concat(data).reset_index(drop=True)

        except ValueError:
            print("No data retrieved for the epoch span")
            data = pd.DataFrame()

        return data

    def get_validators_vote_credits(self):
        """Extract all the validators and their balance per epoch. NB: This method only work since epoch 275."""

        validators = self.get_validators_snapshot()
        data = validators.explode("epochCredits")

        data["epoch"] = [x[0] if type(x) == list else None for x in data["epochCredits"]]
        data["prev_vote_credits"] = [x[2] if type(x) == list else None for x in data["epochCredits"]]
        data["post_vote_credits"] = [x[1] if type(x) == list else None for x in data["epochCredits"]]

        data = data.drop("epochCredits", axis=1).reset_index(drop=True)

        return data

    def get_delegators_snapshot(self, vote_key: str = None):
        """Extract all the delegator of a specific validator program.

        The address to be used is one of the validators' votePubkey values.
        """

        if not vote_key:
            vote_key = self.validator_vote_key

        STAKE_PROGRAM_ID: PublicKey = PublicKey("Stake11111111111111111111111111111111111111")

        memcmp_opts = [MemcmpOpts(offset=124, bytes=vote_key)]
        response = self.api.get_program_accounts(
            STAKE_PROGRAM_ID,
            encoding="jsonParsed",
            data_size=200,
            memcmp_opts=memcmp_opts,
        )

        data = list()
        for d in response.get("result"):
            try:
                info = dict()
                info["program"] = d["account"]["data"]["program"]
                info["lamports"] = d["account"]["lamports"]
                info["rentEpoch"] = d["account"]["rentEpoch"]

                meta_info = dict()
                meta_info["staker"] = d["account"]["data"]["parsed"]["info"]["meta"]["authorized"]["staker"]
                meta_info["withdrawer"] = d["account"]["data"]["parsed"]["info"]["meta"]["authorized"]["withdrawer"]
                meta_info["custodian"] = d["account"]["data"]["parsed"]["info"]["meta"]["lockup"]["custodian"]
                meta_info["rentExemptReserve"] = d["account"]["data"]["parsed"]["info"]["meta"]["rentExemptReserve"]

                delegation_info = d["account"]["data"]["parsed"]["info"]["stake"]["delegation"]
                delegation_info["creditsObserved"] = d["account"]["data"]["parsed"]["info"]["stake"]["creditsObserved"]

                info.update(meta_info)
                info.update(delegation_info)
                data.append(info)

            except Exception as e:
                print(e)
                continue

        data = pd.DataFrame(data).reset_index(drop=True)
        data = data.replace({str(np.iinfo(np.uintp).max): None})
        data["inserted_at"] = datetime.datetime.now()
        return data

    def get_delegators_stakes(self, vote_key: str = None):
        """Extract the full staking history of a validator node's exhaustive list of delegators from Solanascan."""

        vote_key = vote_key if vote_key else self.validator_vote_key
        delegators = self.get_delegators_snapshot(vote_key)
        url = "https://public-api.solscan.io/account/stakeAccounts?"
        headers = self.solscan_headers
        data = list()

        for delegator_address in tqdm(delegators["staker"]):
            response = requests.get(url, headers=headers, params=dict(account=delegator_address)).json()
            stake_accounts = pd.DataFrame(response.values())
            stake_activations = [self.api.get_stake_activation(stake_account).get("result") for stake_account in stake_accounts["stakeAccount"]]
            df = pd.concat([stake_accounts, pd.DataFrame(stake_activations)], axis=1)
            data.append(df)

        data = pd.concat(data).reset_index(drop=True)
        return data

    def get_delegators_rewards(self, addresses: list = None, start_epoch: int = None):
        """Extract the inflation reward for all the ledger delegators."""

        if not addresses:
            addresses = self.get_delegators_stakes()["stakeAccount"].tolist()

        if not start_epoch:
            start_epoch = self.get_start_epoch("solana_delegators_rewards", "epoch")

        data = list()
        chunk_size = 100
        addresses_chunks = [addresses[i : i + chunk_size] for i in range(0, len(addresses), chunk_size)]

        for epoch in tqdm(range(start_epoch, self.current_epoch)):
            # pull data for the next epoch of what's in the db, until the previous epoch from current
            for chunk in addresses_chunks:

                url = self.figment_api_url
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getInflationReward",
                    "params": [chunk, {"epoch": epoch}],
                }
                response = requests.post(url, headers=self.headers, json=payload).json().get("result")

                if not response:
                    df = pd.DataFrame()
                else:
                    response = [x if x is not None else dict() for x in response]
                    df = pd.DataFrame(response)
                    df["stake_account"] = chunk
                    df["epoch"] = epoch
                    df["inserted_at"] = self.execution_timestamp

                data.append(df)

        try:
            data = pd.concat(data).reset_index(drop=True)

        except ValueError:
            print("No data retrieved for the epoch span")
            data = pd.DataFrame()

        return data


if __name__ == "__main__":
    client = SolanaAPI()
