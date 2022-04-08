import React from "react";
import "../../App.css";
import "./Transfers.css";
import Footer from "../common_elements/Footer";

function Transfers() {
  return (
    <>
      <div className="transfers">

        <div className="transfers-header">
          <h1>Transfers</h1>
          <div>
            <p className="transfers-header-text">
              Feeling like trying few transactions while making a happy friend? Here's
              the space where you can realize the transactions you'd like on Solana network.
            </p>
          </div>
        </div>

        <div className="transfers-body">
          <div className="transfers-left-column">
            <div className="transfers-item transfers-item-1">
              <p>
                This container will hold the wallet information, i.e. the amount
                available, the corresponding amount in euros, us dollars, and
                other currencies. It'll display also the exchange rates.
              </p>
            </div>

            <div className="transfers-item transfers-item-2">
              <p>
                This container will hold the information about the number of
                transactions realized by the user, a ranking of the recipient
                addresses by transactions number.
              </p>
            </div>
          </div>

          <div className="transfers-mid-column transfers-item">
            <p>
              This container will hold the interface to realize a transfer from
              one recipient to another.
            </p>
          </div>

          <div className="transfers-right-column">
            <div className="transfers-item transfers-item-1"> Item 5</div>
            <div className="transfers-item transfers-item-2"> Item 6</div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
export default Transfers;
