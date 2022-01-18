// Emission
// Registers:
// 4: Long: Total amount staked
// 5: Long: Checkpoint
// 6: Long: Stakers
// 7: Long: Emission amount
// Assets:
// 0: Emission NFT: Identifier for emit box
// 1: Staked Tokens (ErgoPad): Tokens to be distributed
{{
    val stakeStateNFT = fromBase64("{stakeStateNFT}")
    val stakeTokenID = fromBase64("{stakeTokenID}")
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == {{stakeStateContractHash}}

    def isStakeBox(box: Box) = box.tokens(0)._1 == stakeTokenID
    def isCompoundBox(box: Box) = isStakeBox(box) || box.tokens(0)._1 == SELF.tokens(0)._1 || box.tokens(0)._1 == stakeStateNFT

    if (stakeStateInput && INPUTS(2).id == SELF.id) {{ // Emit transaction
        sigmaProp(allOf(Coll(
            //Stake State, Stake Pool, Emission (self) => Stake State, Stake Pool, Emission
            OUTPUTS(2).propositionBytes == SELF.propositionBytes,
            OUTPUTS(2).R4[Long].get == INPUTS(1).R4[Long].get,
            OUTPUTS(2).R5[Long].get == INPUTS(0).R5[Long].get,
            OUTPUTS(2).R6[Long].get == INPUTS(0).R6[Long].get,
            OUTPUTS(2).R7[Long].get == INPUTS(1).R4[Long],
            OUTPUTS(2).tokens(0)._1 == SELF.tokens(0)._1,
            OUTPUTS(2).tokens(1)._2 == OUTPUTS(2).R7[Long].get
        )))
    }} else {{
    if (stakeStateInput && INPUTS(1).id == SELF.id) {{ // Compound transaction
        // Stake State, Emission (SELF), Stake*N => Stake State, Emission, Stake*N
        val stakeBoxes = INPUTS.filter({{(box: Box) => isStakeBox(box)}}).size
        val stakeInOut = OUTPUTS.filter({{(box: Box) => isStakeBox(box)}}).size == stakeBoxes
        sigmaProp(allOf(Coll(
            stakeInOut,
            OUTPUTS(1).propositionBytes == SELF.propositionBytes,
            OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
            OUTPUTS(1).tokens.size == 1 || OUTPUTS(1).tokens(1)._1 == stakedTokenID, // In case we have used up the last tokens for this cycle
            OUTPUTS(1).R4[Long].get == SELF.R4[Long].get,
            OUTPUTS(1).R5[Long].get == SELF.R5[Long].get,
            OUTPUTS(1).R6[Long].get == SELF.R6[Long].get - stakeBoxes,
            OUTPUTS(1).R7[Long].get == SELF.R7[Long].get
        )))
    }} else {{
        sigmaProp(false)
    }}}}
}}