{{
    val dataTokenId = fromBase64("{dataTokenId}")
    val updateTokenId = fromBase64("{updateTokenId"})
    val updateFrequency = {updateFrequency}
    val blockTime = CONTEXT.preHeader.timestamp

    val selfOutput = OUTPUTS(0).propositionBytes == SELF.propositionBytes &&
                        OUTPUTS(0).tokens.size == 1 &&
                        OUTPUTS(0).tokens(0)._1 == dataTokenId &&
                        OUTPUTS(0).R4[Long].get >= 0 &&
                        OUTPUTS(0).R5[Long].get == SELF.R5[Long].get + updateFrequency &&
                        OUTPUTS(0).R5[Long].get < blockTime

    val updateTokenOutput = OUTPUTS(1).tokens(0)._1 == updateTokenId

    sigmaProp(selfOutput && updateTokenOutput)
}}