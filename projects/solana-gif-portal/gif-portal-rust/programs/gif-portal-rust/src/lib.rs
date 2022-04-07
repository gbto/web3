use anchor_lang::prelude::*;

declare_id!("2Ph9ShJ7wV3PwPdrFcFaJZm53t33CSBYkv3DEB56cdsq");

#[program]
mod gif_portal_rust {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        // Get a reference to the account structure
        let base_account = &mut ctx.accounts.base_account;
        // Initialize total_gifs property
        base_account.total_gifs = 0;
        Ok(())
    }

    pub fn add_gif(ctx: Context<AddGif>, gif_link: String) -> Result <()> {
        // Get a reference to the account and user structures
        let base_account = &mut ctx.accounts.base_account;
        let user = &mut ctx.accounts.user;

        // Build the item structure
        let item = ItemStruct {
        gif_link: gif_link.to_string(),
        user_address: *user.to_account_info().key,
        };

        // Add it to the gif_list vector
        base_account.gif_list.push(item);
        base_account.total_gifs += 1;
        Ok(())
  }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = user, space = 9000)]
    pub base_account: Account<'info, BaseAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program <'info, System>,
}

// Specify required data in the AddGif Context
#[derive(Accounts)]
pub struct AddGif<'info> {

    #[account(mut)]
    pub base_account: Account<'info, BaseAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
}

// Create a custom struct to work with
#[derive(Debug, Clone, AnchorSerialize, AnchorDeserialize)] // Tells anchor how to deserialize the struc
pub struct ItemStruct {
    pub gif_link: String,
    pub user_address: Pubkey,
}

// Tell Solana what to store on this account
#[account]
pub struct BaseAccount {
    pub total_gifs: u64,
    pub gif_list: Vec<ItemStruct>,  // Attach a Vector of type ItemStruct to the account
}
