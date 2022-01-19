{{
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
    
    val blockTime = CONTEXT.preHeader.timestamp
    val stakedTokenID = fromBase64("{stakedTokenID}")
    val stakePoolNFT = fromBase64("{stakePoolNFT}")
    val emissionNFT = fromBase64("{emissionNFT}")
    val cycleDuration = SELF.R8[Long].get

    def isStakeBox(box: Box) = box.tokens(0)._1 == SELF.tokens(1)._1
    def isCompoundBox(box: Box) = isStakeBox(box) || box.tokens(0)._1 == emissionNFT || box.tokens(0)._1 == SELF.tokens(0)._1

    val selfReplication = allOf(Coll(
        OUTPUTS(0).propositionBytes == SELF.propositionBytes,
        OUTPUTS(0).value == SELF.value,
        OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
        OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2,
        OUTPUTS(0).tokens(1)._1 == SELF.tokens(1)._1,
        OUTPUTS(0).R8[Long].get == cycleDuration,
        OUTPUTS(0).tokens.size == 2
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
            // Stake Key (User)
            OUTPUTS(2).propositionBytes == INPUTS(1).R4[Coll[Byte]].get,
            OUTPUTS(2).tokens(0)._2 == 1
        )))
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
            OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
        )))
    }} else {{
    if (INPUTS(1).tokens(0)._1 == emissionNFT) {{ // Compound transaction
        // Stake State (SELF), Emission, Stake*N => Stake State, Emission, Stake*N
        val validInputs = INPUTS.filter({{(box: Box) => isCompoundBox(box)}}).size == INPUTS.size
        val validOutputs = OUTPUTS.filter({{(box: Box) => isCompoundBox(box)}}).size == OUTPUTS.size-1 // Miner output
        sigmaProp(allOf(Coll(
            validInputs,
            validOutputs,
            selfReplication,
            //Stake State
            OUTPUTS(0).R4[Long].get == SELF.R4[Long].get + (INPUTS(1).tokens(1)._2 - (if (OUTPUTS(1).tokens.size == 1) 0L else OUTPUTS(1).tokens(1)._2)),
            OUTPUTS(0).R5[Long].get == SELF.R5[Long].get,
            OUTPUTS(0).R6[Long].get == SELF.R6[Long].get,
            OUTPUTS(0).R7[Long].get == SELF.R7[Long].get,
            OUTPUTS(0).R8[Long].get == SELF.R8[Long].get,
            OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
        )))
    }} else {{
    if (SELF.R6[Long].get > OUTPUTS(0).R6[Long].get) {{ // Unstake
        // Stake State (SELF), Stake, Stake Key Box => Stake State, User Wallet
        val timeInWeeks = (blockTime - INPUTS(1).R6[Long].get)/1000/3600/24/7
        val penalty =   if (timeInWeeks > 8) 0L else 
                        if (timeInWeeks > 6) INPUTS(1).tokens(1)._2*5/100 else 
                        if (timeInWeeks > 4) INPUTS(1).tokens(1)._2*125/1000 else 
                        if (timeInWeeks > 2) INPUTS(1).tokens(1)._2*20/100 else
                        INPUTS(1).tokens(1)._2*25/100
        sigmaProp(allOf(Coll(
            selfReplication,
            //Stake State
            OUTPUTS(0).R4[Long].get == SELF.R4[Long].get-INPUTS(1).tokens(1)._2,
            OUTPUTS(0).R5[Long].get == SELF.R5[Long].get,
            OUTPUTS(0).R6[Long].get == SELF.R6[Long].get-1L,
            OUTPUTS(0).R7[Long].get == SELF.R7[Long].get,
            OUTPUTS(0).R8[Long].get == SELF.R8[Long].get,
            OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2+1,
            //User wallet
            OUTPUTS(1).propositionBytes == INPUTS(2).R5[Coll[Byte]].get,
            OUTPUTS(1).tokens(1)._1 == INPUTS(1).tokens(1)._1,
            OUTPUTS(1).tokens(1)._2 == INPUTS(1).tokens(1)._2 - penalty
        )))
    }} else {{
        sigmaProp(false)
    }}
    }}
    }}
    }}
}}