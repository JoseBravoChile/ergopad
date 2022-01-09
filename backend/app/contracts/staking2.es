{{
    val blockTime = CONTEXT.preHeader.timestamp
    val dataTokenId = fromBase64("{dataTokenId}")
    val stakingKey = fronBase64("{stakingKeyId}")
    val totalStaked = dataInputs(0).R4[Long].get
    val initialStakePoolValue = INPUTS(0).R5[Long].get
    val stakePeriods = INPUTS(0).R6[Long].get
    val timeInWeeks = (blockTime - SELF.R5[Long].get)/1000/3600/24/7
    val stakePoolEmission = initialStakePoolValue/stakePeriods
    val buyerPK = proveDlog(deodePoint(SELF.R4[Coll[Byte]].get)) //probably doesnt work
    val penalty = if timeInWeeks > 8 0 else if timeInWeeks > 6 SELF.tokens(0)._2*5/100 else if timeInWeeks > 4 SELF.tokens(0)._2*125/1000 else if timeInWeeks > 2 SELF.tokens(0)._2*20/100 else SELF.tokens(0)._2*25/100
    val reward = stakePoolEmission*SELF.tokens(0)._2/totalStaked

    //Make sure we use the correct datainput
    val correctDataInput = dataInputs(0).tokens(0)._1 == dataTokenId

    //Does the output contain a box with the correct amount of tokens
    val stakeOutput = OUTPUTS.exists({{(box: Box) => box.propositionBytes == SELF.propositionBytes &&
                                                    box.value == SELF.value &&
                                                    box.tokens(0)._1 == SELF.tokens(0)._1 &&
                                                    box.tokens(0)._2 == SELF.tokens(0)._2 + reward}})

    //Is there an input with a stakingKey
    val stakingKeyHolder = INPUTS(0).tokens(0)._1 == stakingKey &&
                            OUTPUTS(1).tokens(0)._1 == INPUTS(0).tokens(0)._1 &&
                            OUTPUTS(1).tokens(0)._2 == INPUTS(0).tokens(0)._2 &&
                            OUTPUTS(1).propositionBytes == INPUTS(0).propositionBytes

    //Is there an output with the correct unstake amount                        
    val unstakeOutput = OUTPUTS(0).propositionBytes == SELF.R4[Coll[Bytes]].get &&
                        OUTPUTS(0).value == SELF.value &&
                        OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1 &&
                        OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2 - penalty


    sigmaProp((correctDataInput && stakeOutput) || (unstakeOutput && (stakingKeyHolder || buyerPK)))
}}