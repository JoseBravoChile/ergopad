{{
    // Stake
    // Registers:
    // 4: Long: Checkpoint
    // 5: Coll[Byte]: Stake Key ID to be used for unstaking
    // Assets:
    // 0: Stake Token: 1 token to prove this is a legit stake box
    // 1: Staked Token (ErgoPad): The tokens staked by the user
    
    val stakeStateNFT = fromBase64("{stakeStateNFT}")
    val emissionNFT = fromBase64("{emissionNFT")
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == {{stakeStateContractHash}}

    if (INPUTS(1).tokens(0)._1 == emissionNFT) {{ // Compound transaction
        // Stake State, Emission, Stake*N (SELF) => Stake State, Emission, Stake * N
        val selfReplications = OUTPUTS.filter({{(box: Box) => box.R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get}})
        sigmaProp(allOf(Coll(
            selfReplications.size == 1,
            stakeStateInput,
            selfReplications(0).propositionBytes == SELF.propositionBytes,
            selfReplications(0).R4[Long].get == SELF.R4[Long].get + 1,
            selfReplications(0).R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get,
            selfReplications(0).tokens(0)._1 == SELF.tokens(0)._1,
            selfReplications(0).tokens(1)._1 == SELF.tokens(1)._1,
            selfReplications(0).tokens(1)._2 == SELF.tokens(1)._2 + (INPUTS(1).R7[Long].get * SELF.tokens(1)._2 / INPUTS(1).R4[Long].get)
        )))
    }} else {{
    if (INPUTS(1).id == SELF.id) {{ // Unstake
        sigmaProp(stakeStateInput) //Stake state handles logic here to minimize stake box size
    }} else {{
        sigmaProp(false)
    }}
    }}
}}