import React from "react";
import { slide as Sidebar } from "react-burger-menu";
import "./Sidebar.css";

export default (props) => {
  return (
    <Sidebar>
      <a className="menu-item" href="/">
        Home
      </a>
      <a className="menu-item" href="/transfers">
        Transfers
      </a>
      <a className="menu-item" href="/wallet">
        Wallet
      </a>
      <a className="menu-item" href="/others">
        Others
      </a>
    </Sidebar>
  );
};
