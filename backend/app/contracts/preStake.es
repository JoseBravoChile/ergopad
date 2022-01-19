{{
    // preStake
    // Registers:
    // 4: Coll[Byte]: Ergotree of user wallet
    // Assets
    // 0: ErgoPad: Amount of ergopad the user wants to stake
    
    val buyerPK = PK("{buyerWallet}")
    val stakedTokenID = fromBase64("{stakedTokenID}")
    val stakeStateNFT = fromBase64("{stakeStateNFT}")
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == {{stakeStateContractHash}}
    if (stakeStateInput) {{ // Stake transaction
    //Stake State, preStake (SELF) => Stake State, Stake, User Wallet
        sigmaProp(allOf(Coll(
            // Stake
            blake2b256(OUTPUTS(1).propositionBytes) == {{stakeContractHash}},
            OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1,
            OUTPUTS(1).tokens(0)._2 == 1,
            OUTPUTS(1).tokens(1)._1 == stakedTokenID == INPUTS(1).tokens(0)._1,
            OUTPUTS(1).tokens(1)._2 == INPUTS(1).tokens(0)._2
        )))
    }} else {{
        val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 2000000
        sigmaProp(OUTPUTS(0).value >= total && 
        OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
        OUTPUTS.size == 2)
    }}
}}