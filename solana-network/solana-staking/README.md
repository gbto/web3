# SUMMARY

Solana is an open source project implementing a new, high-performance, permissionless blockchain. The Solana Foundation is based in Geneva, Switzerland and maintains the [open source project](https://docs.solana.com/introduction).

<br><br>

# 1. STAKING MECANISM

https://docs.solana.com/cluster/stake-delegation-and-rewards

A primary role of a validator is to submit votes on new blocks produced. If a validator has a high vote accepted rate then that validator will earn close to the highest possible reward for the stake behind it. All validators drop a few votes here and there due to factors outside their control. But the most performant validators get the most votes accepted.

The rewards per epoch is fixed and must be evenly divided among all staked nodes according to their relative stake weight (stake proportional) and participation. Staking yields are based on the current inflation rate, total number of SOL staked, and individual validator uptime and commission. A validator’s commission fee is the percentage fee paid to validators from network inflation. Validator uptime is defined by a validator’s voting. One vote credit is earned for each successful validator vote and are tallied at the end of the epoch for reward calculation.

The validator owns a Vote account that:
- tracks validator votes, counts validator generated credits, and provides any additional validator specific state.
- is not aware of any stakes delegated to it and has no staking weight.
<br><br>

# 2. REWARDS MECANISM

Most basic operations on the Solana network are performed by [native programs](https://docs.solana.com/developing/runtime-facilities/programs). The rewards process is split into two on-chain programs:
- The Vote program solves the problem of making stakes slashable. Validators interact non-stop with the program by making vote transactions, which represents a very large amount of the volume making irrelevant to decode transactions.
- The Stake program acts as custodian of the rewards pool and provides for passive delegation. It is responsible for paying rewards to staker and voter when shown that a staker's delegate has participated in validating the ledger.
<br><br>

# 3. REWARDS TRACKING

Solana staking rewards are paid at each epoch boundary (approximately once every 2.5 days) and are automatically re-staked - that is, they are added to the active delegation of the stake account they are paid out to.

We can use the Solana RPC API - [`getInflationReward`](https://docs.solana.com/developing/clients/jsonrpc-api#getinflationreward) method to obtain the rewards of a list of validators for a specific epoch.

Example Response:

```jsx
{
    "jsonrpc": "2.0",
    "result": [
        {
            "amount": 161103632916,
            "commission": 7,
            "effectiveSlot": 101088000,
            "epoch": 233,
            "postBalance": 1911605123734
        }
    ],
    "id": 1
}
```

Using this RPC call, we can retrieve the reward payout for a given epoch (`amount` is in lamports, to be divided by 10^9 to convert in SOL) and the stake account balance after reward payout (`postBalance`).

The process is to:
1. extract a snapshot of the validators with get_vote_accounts method to retrieve the vote public keys
2. extract the rewards per epoch with the staking program's votePubkey
3. extract a snapshot of the delegators belonging to a staking program with the get_program_account method
4. extract all the staking accounts tied to each delegators of a given validator
5. extract the rewards per epoch with the delegators staking account addresses

<br><br>

# 4. EFFECTIVE REWARD RATE

If you want to calculate an effective rewards rate, you will need the epoch start and end times.   You can get these timestamps using the [`getBlockTime`](https://docs.solana.com/developing/clients/jsonrpc-api#getblocktime) endpoint.

Example Response:

```jsx
{
    "jsonrpc": "2.0",
    "result": 1634956645,
    "id": 1
}
```

Solana epochs are 432,000 blocks each, so you will need to get a start time using block number `rewardEpcoch * 432000` and an end time using block number `(rewardEpoch + 1) * 432000 -1`

Note:  Some blocks do not have timestamps as they are only recorded if enough validators to form a consensus provide one.  You may have to step through blocks in sequence until you find one that returns a timestamp, but given block times of around 1/2 second, it should not make a significant difference in the calculations.
