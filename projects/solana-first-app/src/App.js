import React from "react";
import Navbar from "./components/common_elements/Navbar";
import Sidebar from './components/common_elements/Sidebar';
import Home from './components/pages/Home';
import Transfers from './components/pages/Transfers';
import SignUp from './components/pages/SignUp';

import './App.css';
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom';

const App = () =>  {
  return (
    <>
      <Router>
        <Navbar />
        <Sidebar
          pageWrapId={"page-wrap"}
          outerContainerId={"outer-container"}
        />

        <Switch>
          <Route path="/" exact component={Home} />
          <Route path="/transfers" component={Transfers} />
          <Route path="/sign-up" component={SignUp} />
        </Switch>
      </Router>
    </>
  );
}

export default App;
