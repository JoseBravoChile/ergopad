{{
    val dataTokenId = fromBase64("{dataTokenId}")
    val stakedTokenId = fronBase64("{stakedTokenId}")
    val blockTime = CONTEXT.preHeader.timestamp

    //Add a filter for checking tokenid == stakedTokenId
    val totalStakedTokenInput = INPUTS.fold(0L,{{(z: Long, box: Box) => z+box.tokens.fold(0L,{{(x: Long, token: (Coll[Byte], Long)) => token._2}})}})

    //Make sure we use the correct datainput
    val correctDataInput = dataInputs(0).tokens(0)._1 == dataTokenId

    //Ensure we keep a stakePool box for the next round
    val selfOutput = OUTPUTS(0).propositionBytes == SELF.propositionBytes &&
                        OUTPUTS(0).R4[Coll[Byte]].get == SELF.R4[Coll[Byte]].get

    //Only staking boxes that have not participated in this round yet are qualified
    val qualifiedStakingBoxes = !(INPUTS.exists({{(box: Box) => box.propositionBytes == SELF.R4[Coll[Byte]].get && box.creationInfo._1 > dataInputs(0).creationInfo._1}}))

    //Only one output is allowed to be non-staking (the miner fee box)
    val qualifiedOutputs = OUTPUTS.filter({{(box: Box) => !(box.propositionBytes == SELF.propositionBytes || box.propositionBytes == SELF.R4[Coll[Byte]].get)}}).size == 1

    sigmaProp(correctDataInput && selfOutput && qualifiedStakingBoxes && qualifiedOutputs)
}}