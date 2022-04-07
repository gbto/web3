const anchor = require("@project-serum/anchor");

const { SystemProgram } = anchor.web3;

const main = async () => {
  console.log("🚀 Starting test...");

  // Create and set the provider
  const provider = anchor.Provider.env();
  anchor.setProvider(provider);

  // Access the solana program from the workspace
  const program = anchor.workspace.GifPortalRust;

  // Create an account keypair for our program to use.
  const baseAccount = anchor.web3.Keypair.generate();

  // Call start_stuff_off and pass it the params it needs
  let tx = await program.rpc.initialize({
    accounts: {
      baseAccount: baseAccount.publicKey,
      user: provider.wallet.publicKey,
      systemProgram: SystemProgram.programId,
    },
    signers: [baseAccount],
  });
  console.log("📝 Your transaction signature", tx);

  // Fetch data from the account
  let account = await program.account.baseAccount.fetch(baseAccount.publicKey);
  console.log("👀 GIF Count", account.totalGifs.toString());

  // Call add_gif
  await program.rpc.addGif("insert_a_giphy_link_here", {
    accounts: {
      baseAccount: baseAccount.publicKey,
      user: provider.wallet.publicKey,
    },
  });

  // Call the account
  account = await program.account.baseAccount.fetch(baseAccount.publicKey);
  console.log("👀 GIF Count", account.totalGifs.toString());

  // Access gif_list on the account
  console.log("👀 GIF List", account.gifList);
};

const runMain = async () => {
  try {
    await main();
    process.exit(0);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
};

runMain();
