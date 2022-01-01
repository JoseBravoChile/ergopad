{
    val buyerPK = PK("{buyerWallet}")
    val sellerPK = PK("{nodeWallet}")
    val tokenId = fromBase64("{purchaseToken}")
    val timestamp = {timestamp}
    val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 2000000

    val sellerOutput = OUTPUTS(0).propositionBytes == sellerPK.propBytes &&
        ((tokenId.size == 0 && OUTPUTS(0).value == {purchaseTokenAmount}) ||
            (OUTPUTS(0).tokens(0)._2 == {purchaseTokenAmount}L && OUTPUTS(0).tokens(0)._1 == tokenId))

    val returnFunds = OUTPUTS(0).value >= total && 
        OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
        OUTPUTS.size == 2

    sigmaProp((returnFunds || sellerOutput) && HEIGHT < timestamp)
}