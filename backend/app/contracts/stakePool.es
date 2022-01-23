{{
    // Stake Pool
    // Registers:
    // 4: Long: Emission amount per cycle
    // Assets:
    // 0: Stake Pool NFT
    // 1: Remaining Staked Tokens for future distribution (ErgoPad)

    val stakeStateNFT = fromBase64("{stakeStateNFT}")
    val stakeStateContract = fromBase64("{stakeStateContractHash}")
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == stakeStateContract
    if (stakeStateInput && INPUTS(1).id == SELF.id) {{ // Emit transaction
        sigmaProp(allOf(Coll(
            //Stake State, Stake Pool (self), Emission => Stake State, Stake Pool, Emission
            OUTPUTS(1).propositionBytes == SELF.propositionBytes,
            OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
            OUTPUTS(1).tokens(1)._1 == SELF.tokens(1)._1,
            OUTPUTS(1).tokens(1)._2 == SELF.tokens(1)._2 + INPUTS(2).tokens(1)._2 - SELF.R4[Long].get,
            OUTPUTS(1).R4[Long].get == SELF.R4[Long].get
        )))
    }} else {{
        sigmaProp(false)
    }}
}}