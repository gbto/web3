import React from "react";
import "../../App.css";
import "./Home.css";
import Footer from "../common_elements/Footer";

function Home() {
  return (
    <>
      <div className="home">
        <div className="home-header">
          <h1>Welcome back</h1>
          <div className="home-header-text">
            <p className="text-body">
              Welcome to GBTO decentralized app. Here, you'll be able to use you
              wallet to do great things, like sending money to your friends and
              see who amongst them is the luckiest one.
            </p>
          </div>
        </div>

        <div className="home-body">
          <div className="home-items home-box-1 "> Item 1</div>
          <div className="home-items home-box-2 "> Item 2</div>
          <div className="home-items home-box-3 "> Item 3</div>
        </div>
      </div>
      <Footer />
    </>
  );
}
export default Home;
