// Stake State
// Registers:
// 4: Long: Total amount Staked
// 5: Long: Checkpoint
// 6: Long: Stakers
// 7: Long: Last checkpoint timestamp
// 8: Long: Cycle duration
// Assets:
// 0: Stake State NFT: 1
// 1: Stake Token: Stake token to be handed to Stake Boxes
{{
    val blockTime = CONTEXT.preHeader.timestamp
    val stakedTokenID = fromBase64("{stakedTokenID}")
    val stakePoolNFT = fromBase64("{stakePoolNFT}")
    val emissionNFT = fromBase64("{emissionNFT")
    val cycleDuration = SELF.R8[Long].get
    val selfReplication = allOf(Coll(
        OUTPUTS(0).propositionBytes == SELF.propositionBytes,
        OUTPUTS(0).value == SELF.value,
        OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
        OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2,
        OUTPUTS(0).tokens(1)._1 == SELF.tokens(1)._1,
        OUTPUTS(0).R8[Long].get == cycleDuration
    ))
    if (OUTPUTS(2).tokens(0)._1 == SELF.id) {{ // Stake transaction
        // Stake State (SELF), preStake => Stake State, Stake, Stake Key (User)
        sigmaProp(allOf(Coll(
            selfReplication,
            // Stake State
            OUTPUTS(0).R4[Long].get == SELF.R4[Long].get + OUTPUTS(1).tokens(1)._2,
            OUTPUTS(0).R5[Long].get == SELF.R5[Long].get,
            OUTPUTS(0).R6[Long].get == SELF.R6[Long].get+1,
            OUTPUTS(0).R7[Long].get == SELF.R7[Long].get,
            OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2-1,
            // Stake
            blake2b256(OUTPUTS(1).propositionBytes) == {{stakeContractHash}},
            OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1,
            OUTPUTS(1).tokens(0)._2 == 1,
            OUTPUTS(1).tokens(1)._1 == stakedTokenID == INPUTS(1).tokens(0)._1,
            OUTPUTS(1).tokens(1)._2 == INPUTS(1).tokens(0)._2,
            // Stake Key (User)
            OUTPUTS(2).propositionBytes == INPUTS(1).R4[Coll[Byte]].get,
            OUTPUTS(2).tokens(0)._2 == 1
        ))
    }} else {{
    if (INPUTS(1).tokens(0)._1 == stakePoolNFT) {{ // Emit transaction
        // Stake State (SELF), Stake Pool, Emission => Stake State, Stake Pool, Emission
        sigmaProp(allOf(Coll(
            selfReplication,
            //Emission INPUT
            INPUTS(2).tokens(0)._1 == emissionNFT,
            INPUTS(2).R5[Long].get == SELF.R5[Long].get,
            INPUTS(2).R6[Long].get == 0L,
            //Stake State
            OUTPUTS(0).R4[Long].get == SELF.R4[Long].get,
            OUTPUTS(0).R5[Long].get == SELF.R5[Long].get + 1L,
            OUTPUTS(0).R6[Long].get == SELF.R6[Long].get,
            OUTPUTS(0).R7[Long].get == SELF.R7[Long].get + SELF.R8[Long].get,
            OUTPUTS(0).R8[Long].get == SELF.R8[Long].get,
            OUTPUTS(0).R7[Long].get < blockTime,
            //Stake Pool
            OUTPUTS(1).propositionBytes == INPUTS(1).propositionBytes,
            OUTPUTS(1).tokens(0)._1 == stakePoolNFT,
            OUTPUTS(1).tokens(1)._1 == stakedTokenID == INPUTS(1).tokens(1)._1,
            OUTPUTS(1).tokens(1)._2 == INPUTS(1).tokens(1)._2 + INPUTS(2).tokens(1)._2 - OUTPUTS(1).R4[Long].get,
            OUTPUTS(1).R4[Long].get == INPUTS(1).R4[Long].get,
            //Emission
            OUTPUTS(2).propositionBytes == INPUTS(2).propositionBytes,
            OUTPUTS(2).R4[Long].get == SELF.R4[Long].get,
            OUTPUTS(2).R5[Long].get == OUTPUTS(0).R5[Long].get,
            OUTPUTS(2).R6[Long].get == SELF.R6[Long].get,
            OUTPUTS(2).R7[Long].get == INPUTS(1).R4[Long],
            OUTPUTS(2).tokens(0)._1 == emissionNFT,
            OUTPUTS(2).tokens(1)._1 == INPUTS(1).tokens(1)._1,
            OUTPUTS(2).tokens(1)._2 == OUTPUTS(2).R7[Long].get
        )))
    }} else {{
    if () {{ // Compound transaction
    }} else {{
    if () {{ // Unstake
    }} else {{
        sigmaProp(false)
    }}
    }}
    }}
    }}
}}