/*
 * We are going to be using the useEffect hook!
 */
import React, { useEffect, useState } from "react";
// import githubLogo from "./assets/github-logo.png";
import "./App.css";
import kp from "./keypair.json";
import { Connection, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { Program, Provider, web3 } from "@project-serum/anchor";

import idl from "./idl.json";

// SystemProgram is a reference to the Solana runtime
const { SystemProgram, Keypair } = web3;

// Create a keypair for the account that will hold the GIF data
// let baseAccount = Keypair.generate();
const arr = Object.values(kp._keypair.secretKey);
const secret = new Uint8Array(arr);
const baseAccount = web3.Keypair.fromSecretKey(secret);

// Get the program's id from the Solana program IDL file
const programID = new PublicKey(idl.metadata.address);

// Set the network to devnet
const network = clusterApiUrl("devnet");

// Controls how we want to acknowledge when a transaction is "done"
const opts = {
  preflightCommitment: "processed",
};

// Declare constants used on the front end
const GITHUB_NAME = "blockchain";
const GITHUB_REPO = "blockchain/tree/main";
const GITHUB_LINK = `https://github.com/qgaborit-ledger/${GITHUB_REPO}`;

const App = () => {
  // States
  const [walletAddress, setWalletAddress] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [gifList, setGifList] = useState([]);
  /*
   * This function holds the logic for deciding if a Phantom Wallet is
   * connected or not
   */
  const checkIfWalletIsConnected = async () => {
    try {
      const { solana } = window;

      if (solana) {
        if (solana.isPhantom) {
          console.log("Phantom wallet found!");
          /*
           * The solana object gives us a function that will allow us to connect
           * directly with the user's wallet!
           */
          const response = await solana.connect({ onlyIfTrusted: true });
          console.log(
            "Connected with Public Key:",
            response.publicKey.toString()
          );
          /*
           * Set the user's publicKey in state to be used later!
           */
          setWalletAddress(response.publicKey.toString());
        }
      } else {
        alert("Solana object not found! Get a Phantom Wallet 👻");
      }
    } catch (error) {
      console.error(error);
    }
  };

  /*
   * We will write the logic for this next!
   */
  const connectWallet = async () => {
    const { solana } = window;

    if (solana) {
      const response = await solana.connect();
      console.log("Connected with Public Key:", response.publicKey.toString());
      setWalletAddress(response.publicKey.toString());
    }
  };
  /*
   * Create a provider of authenticated connection to Solana
   */
  const getProvider = () => {
    const connection = new Connection(network, opts.preflightCommitment);
    const provider = new Provider(
      connection,
      window.solana,
      opts.preflightCommitment
    );
    return provider;
  };
  const createGifAccount = async () => {
    try {
      const provider = getProvider();
      const program = new Program(idl, programID, provider);
      console.log("ping");
      await program.rpc.initialize({
        accounts: {
          baseAccount: baseAccount.publicKey,
          user: provider.wallet.publicKey,
          systemProgram: SystemProgram.programId,
        },
        signers: [baseAccount],
      });
      console.log(
        "Created a new BaseAccount w/ address:",
        baseAccount.publicKey.toString()
      );
      await getGifList();
    } catch (error) {
      console.log("Error creating BaseAccount account:", error);
    }
  };
  /*
   * Handles input and consequent actions
   */
  const onInputChange = (event) => {
    const { value } = event.target;
    setInputValue(value);
  };
  const sendGif = async () => {
    if (inputValue.length === 0) {
      console.log("No gif link given!");
      return;
    }
    setInputValue("");
    console.log("Gif link:", inputValue);
    try {
      const provider = getProvider();
      const program = new Program(idl, programID, provider);

      await program.rpc.addGif(inputValue, {
        accounts: {
          baseAccount: baseAccount.publicKey,
          user: provider.wallet.publicKey,
        },
      });
      console.log("GIF successfully sent to program", inputValue);

      await getGifList();
    } catch (error) {
      console.log("Error sending GIF:", error);
    }
  };
  /*
   * Render a UI when the user hasn't connected their wallet to the app
   */
  const renderNotConnectedContainer = () => (
    <button
      className="cta-button connect-wallet-button"
      onClick={connectWallet}
    >
      Connect to Wallet
    </button>
  );
  /*
   * Render a UI when the user has connected their wallet to the app
   */
  const renderConnectedContainer = () => {
    // If we hit this, it means the program account hasn't been initialized.
    if (gifList === null) {
      return (
        <div className="connected-container">
          <button
            className="cta-button submit-gif-button"
            onClick={createGifAccount}
          >
            Do One-Time Initialization For GIF Program Account
          </button>
        </div>
      );
    }
    // Otherwise, we're good! Account exists. User can submit GIFs.
    else {
      return (
        <div className="connected-container">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              sendGif();
            }}
          >
            <input
              type="text"
              placeholder="Enter gif link!"
              value={inputValue}
              onChange={onInputChange}
            />
            <button type="submit" className="cta-button submit-gif-button">
              Submit
            </button>
          </form>
          <div className="gif-grid">
            {/* We use index as the key instead, also, the src is now item.gifLink */}
            {gifList.map((item, index) => (
              <div className="gif-item" key={index}>
                <img src={item.gifLink} />
                <div className="gif-info" key={index}> URL: {item.gifLink} </div>
              </div>
            ))}
          </div>
        </div>
      );
    }
  };
  /*
  *
  */
  const renderGifInformation = () => {
      return <div>

      </div>
  }
  /*
   * Check to see if we have a connected Phantom Wallet when our component first mounts
   */
  useEffect(() => {
    const onLoad = async () => {
      await checkIfWalletIsConnected();
    };
    window.addEventListener("load", onLoad);
    return () => window.removeEventListener("load", onLoad);
  }, []);
  /*
   * Fetch the gifs list from Solana program and add it to the state
   */
  const getGifList = async () => {
    try {
      const provider = getProvider();
      const program = new Program(idl, programID, provider);
      const account = await program.account.baseAccount.fetch(
        baseAccount.publicKey
      );

      console.log("Got the account", account);
      setGifList(account.gifList);
    } catch (error) {
      console.log("Error in getGifList: ", error);
      setGifList(null);
    }
  };
  useEffect(() => {
    if (walletAddress) {
      console.log("Fetching GIF list...");
      getGifList();
    }
  }, [walletAddress]);

  // Return the page HTML
  return (
    <div className="App">
      <div className="container">
        <div className="header-container">
          <p className="header"> GBTO inc.</p>
          <p className="sub-text">Welcome to GBTO's first dApp! ✨</p>
          <p className="sub-text-summary">This application allows users create a personal GIF wall where transactions are executed on Solana network.</p>
          {/* Add the condition to show this only if we DON'T have a wallet address */}
          {!walletAddress && renderNotConnectedContainer()}
          {/* Add the condition to show this only if we DO have a wallet address */}
          {walletAddress && renderConnectedContainer()}
          {/* This was solely added for some styling fanciness */}
          <div
            className={walletAddress ? "authed-container" : "container"}
          ></div>
        </div>
        <div className="footer-container">
          {/* <img alt="Github Logo" className="github-logo" src={githubLogo} /> */}
          <a
            className="footer-text"
            href={GITHUB_LINK}
            target="_blank"
            rel="noreferrer"
          >{`built by @gibboneto at /${GITHUB_NAME}`}</a>
        </div>
      </div>
    </div>
  );
};

export default App;
