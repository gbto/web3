import React from "react";
import "../../App.css";
import "./Wallet.css";
import Footer from "../common_elements/Footer";

function Wallet() {
  return (
    <>
      <div className="wallet">
        <div className="wallet-header">
          <h1>Wallet</h1>
          <div>
            <p className="text-body wallet-box-items">
              Let's have a look to what you've done with your money now. More of
              a gambler person? Betting on any shitcoin random people get
              excited about on twitter? Or maybe DeFi shifu, with thousands of
              transactions per day? You'll find here all the information about
              your Solana wallet!
            </p>
          </div>
        </div>
        <div className="wallet-body"></div>
      </div>
      <Footer />
    </>
  );
}
export default Wallet;
