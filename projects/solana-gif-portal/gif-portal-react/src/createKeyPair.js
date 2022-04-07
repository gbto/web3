/* In order to avoid generating a new account for our program to talk to every time we
* need to have one keypair that all our users share. The keypair will be written directly
* to the file system and anytime people come they'll load the same keypair.
*/

const fs = require("fs");
const anchor = require("@project-serum/anchor");

const account = anchor.web3.Keypair.generate();

fs.writeFileSync("./keypair.json", JSON.stringify(account));
