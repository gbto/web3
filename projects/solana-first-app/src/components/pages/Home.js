import React from "react";
import "../../App.css";
import "./Home.css";
import Footer from "../common_elements/Footer";

function Home() {
  return (
    <>
      <div className="home">
        <div className="home-header">
          <h1>Welcome</h1>
          <div className="home-header-text">
            <p className="text-body home-box-items">
              Welcome to GBTO decentralized app. Here, you'll be able to use you
              wallet to do great things, like sending money to your friends and
              monitor how you're spending on Solana network.
            </p>
          </div>
        </div>

        <div className="home-body">
          <div className="home-items home-box-1 ">
            <div className="home-box-items img">
              <img src="images/img-2.jpg" alt="Solana" />
              <h2>This is the place where it all begins</h2>
              <br></br>
              <p>
                Where everything starts to make sense, where the excitement is
                already beyond any reason and you realize how much shit is
                written on this page.
              </p>
            </div>
          </div>
          <div className="home-items home-box-2 ">
            <div className="home-box-items">
              <img src="images/img-3.jpg" alt="Solana" />
              <h2>This is the place where it all begins</h2>
              <br></br>
              <p>
                Where everything starts to make sense, where the excitement is
                already beyond any reason and you realize how much shit is
                written on this page.
              </p>
            </div>
          </div>
          <div className="home-items home-box-3 ">
            <div className="home-box-items">
              <img src="/images/img-4.jpeg" alt="Solana " />
              <h2>This is the place where it all begins</h2>
              <br></br>
              <p>
                Where everything starts to make sense, where the excitement is
                already beyond any reason and you realize how much shit is
                written on this page.
              </p>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
export default Home;
