import org.ergoplatform.compiler.ErgoScalaCompiler._
import org.ergoplatform.playgroundenv.utils.ErgoScriptCompiler
import org.ergoplatform.playground._
import org.ergoplatform.ErgoBox
import org.ergoplatform.settings.ErgoAlgos
import scorex.crypto.hash.{Blake2b256}
import java.util.Base64
import java.nio.charset.StandardCharsets
import sigmastate.Values.{
  BigIntConstant,
  ByteArrayConstant,
  GroupElementConstant,
  LongConstant,
  LongArrayConstant
}
import org.ergoplatform.ErgoAddress
import org.ergoplatform.appkit.{ErgoContract, ErgoType, ErgoValue, JavaHelpers}
import scorex.crypto.hash.Digest32
import sigmastate.serialization.ErgoTreeSerializer
import special.collection.Coll

object Main extends App {

///////////////////////////////////////////////////////////////////////////////////
// Prepare A Test Scenario //
///////////////////////////////////////////////////////////////////////////////////
// Create a simulated blockchain (aka "Mockchain")
val blockchainSim = newBlockChainSimulationScenario("ErgoPad Staking Scenario")
// Defining the amount of nanoergs in an erg, making working with amounts easier
val nanoergsInErg = 1000000000L
val minErg = 100000L
// Create a new token called ERDoge
val stakedTokenId = blockchainSim.newToken("ErgoPad")
val stakeStateNFT = blockchainSim.newToken("ErgoPad Stake State")
val stakePoolNFT = blockchainSim.newToken("ErgoPad Stake Pool")
val emissionNFT = blockchainSim.newToken("ErgoPad Emission")
val stakeTokenId = blockchainSim.newToken("ErgoPad Stake Token")

// Define the ergopadio wallet
val ergopadio = blockchainSim.newParty("Ergopad.io")

// Define the erdoge buyers
val stakerA = blockchainSim.newParty("Alice")
val stakerB = blockchainSim.newParty("Bob")

val stakeStateScript = s"""
  {
    // Stake State
    // Registers:
    // 4:0 Long: Total amount Staked
    // 4:1 Long: Checkpoint
    // 4:2 Long: Stakers
    // 4:3 Long: Last checkpoint timestamp
    // 4:4 Long: Cycle duration
    // Assets:
    // 0: Stake State NFT: 1
    // 1: Stake Token: Stake token to be handed to Stake Boxes
    
    val blockTime = 99999999999999L//CONTEXT.preHeader.timestamp
    val stakedTokenID = _stakedTokenID
    val stakePoolNFT = _stakePoolNFT
    val emissionNFT = _emissionNFT
    val cycleDuration = SELF.R4[Coll[Long]].get(4)
    
    def isStakeBox(box: Box) = if (box.tokens.size >= 1) box.tokens(0)._1 == SELF.tokens(1)._1 else false
    def isCompoundBox(box: Box) = if (box.tokens.size >= 1) isStakeBox(box) || box.tokens(0)._1 == emissionNFT || box.tokens(0)._1 == SELF.tokens(0)._1 else false

    val selfReplication = allOf(Coll(
        OUTPUTS(0).propositionBytes == SELF.propositionBytes,
        OUTPUTS(0).value == SELF.value,
        OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
        OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2,
        OUTPUTS(0).tokens(1)._1 == SELF.tokens(1)._1,
        OUTPUTS(0).R4[Coll[Long]].get(4) == cycleDuration,
        OUTPUTS(0).tokens.size == 2
    ))
    if (OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1) { // Stake transaction
        // Stake State (SELF), preStake => Stake State, Stake, Stake Key (User)
        sigmaProp(allOf(Coll(
            selfReplication,
            // Stake State
            OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + OUTPUTS(1).tokens(1)._2,
            OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
            OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2)+1,
            OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
            OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2-1
        )))
    } else {
    if (INPUTS(1).tokens(0)._1 == stakePoolNFT && INPUTS.size >= 3) { // Emit transaction
         // Stake State (SELF), Stake Pool, Emission => Stake State, Stake Pool, Emission
         sigmaProp(allOf(Coll(
             selfReplication,
             //Emission INPUT
             INPUTS(2).tokens(0)._1 == emissionNFT,
             INPUTS(2).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
             INPUTS(2).R4[Coll[Long]].get(2) == 0L,
             //Stake State
             OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
             OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1) + 1L,
             OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
             OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3) + SELF.R4[Coll[Long]].get(4),
             OUTPUTS(0).R4[Coll[Long]].get(3) < blockTime,
             OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
         )))
    } else {
    if (INPUTS(1).tokens(0)._1 == emissionNFT) { // Compound transaction
          //Stake State (SELF), Emission, Stake*N => Stake State, Emission, Stake*N
          val leftover = if (OUTPUTS(1).tokens.size == 1) 0L else OUTPUTS(1).tokens(1)._2
          sigmaProp(allOf(Coll(
               selfReplication,
               //Stake State
               OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + INPUTS(1).tokens(1)._2 - leftover,
               OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
               OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
               OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
               OUTPUTS(0).R4[Coll[Long]].get(4) == SELF.R4[Coll[Long]].get(4),
               OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
           )))
     } else {
     if (SELF.R4[Coll[Long]].get(0) > OUTPUTS(0).R4[Coll[Long]].get(0) && INPUTS.size >= 3) { // Unstake
         // Stake State (SELF), Stake, Stake Key Box => Stake State, User Wallet, Stake (optional for partial unstake)
         val remaining = if (OUTPUTS(2).propositionBytes == INPUTS(1).propositionBytes) OUTPUTS(2).tokens(1)._2 else 0L
         val unstaked = INPUTS(1).tokens(1)._2 - remaining
         val timeInWeeks = (blockTime - INPUTS(1).R4[Coll[Long]].get(1))/1000/3600/24/7
         val penalty =  if (timeInWeeks > 8) 0L else 
                         if (timeInWeeks > 6) unstaked*5/100 else 
                         if (timeInWeeks > 4) unstaked*125/1000 else 
                         if (timeInWeeks > 2) unstaked*20/100 else
                         unstaked*25/100
         sigmaProp(allOf(Coll(
             selfReplication,
             //Stake State
             OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0)-unstaked,
             OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
             OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2) - (if (remaining == 0L) 1L else 0L),
             OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
             OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2 + (if (remaining == 0L) 1L else 0L),
             //User wallet
             OUTPUTS(1).propositionBytes == INPUTS(2).propositionBytes,
             OUTPUTS(1).tokens(0)._1 == INPUTS(1).tokens(1)._1,
             OUTPUTS(1).tokens(0)._2 == unstaked - penalty,
             if (remaining > 0L) allOf(Coll(
               //Stake output
               OUTPUTS(2).value == INPUTS(1).value,
               OUTPUTS(2).tokens(0)._1 == INPUTS(1).tokens(0)._1,
               OUTPUTS(2).tokens(0)._2 == INPUTS(1).tokens(0)._2,
               OUTPUTS(2).tokens(1)._1 == INPUTS(1).tokens(1)._1,
               OUTPUTS(2).R4[Coll[Long]].get(0) == INPUTS(1).R4[Coll[Long]].get(0),
               OUTPUTS(2).R4[Coll[Long]].get(1) == INPUTS(1).R4[Coll[Long]].get(1)
              ))
              else true
         )))
     } else {
         sigmaProp(false)
     }
     }
     }
    }
}
""".stripMargin

// Compile the contract with an included `Map` which specifies what the values of given parameters are going to be hard-coded into the contract
val stakeStateContract = ErgoScriptCompiler.compile(
  Map(
    "_stakedTokenID" -> stakedTokenId.tokenId,
    "_stakePoolNFT" -> stakePoolNFT.tokenId,
    "_emissionNFT" -> emissionNFT.tokenId
  ),
  stakeStateScript
)

val emissionScript = """
{
    // Emission
    // Registers:
    // 4:0 Long: Total amount staked
    // 4:1 Long: Checkpoint
    // 4:2 Long: Stakers
    // 4:3 Long: Emission amount
    // Assets:
    // 0: Emission NFT: Identifier for emit box
    // 1: Staked Tokens (ErgoPad): Tokens to be distributed
    
    val stakeStateNFT = _stakeStateNFT
    val stakeTokenID = _stakeTokenID
    val stakedTokenID = _stakedTokenID
    val stakeStateContract = fromBase64(_stakeStateContractHash)
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == stakeStateContract

    if (stakeStateInput && INPUTS(2).id == SELF.id) { // Emit transaction
        sigmaProp(allOf(Coll(
            //Stake State, Stake Pool, Emission (self) => Stake State, Stake Pool, Emission
            OUTPUTS(2).propositionBytes == SELF.propositionBytes,
            OUTPUTS(2).R4[Coll[Long]].get(0) == INPUTS(0).R4[Coll[Long]].get(0),
            OUTPUTS(2).R4[Coll[Long]].get(1) == INPUTS(0).R4[Coll[Long]].get(1),
            OUTPUTS(2).R4[Coll[Long]].get(2) == INPUTS(0).R4[Coll[Long]].get(2),
            OUTPUTS(2).R4[Coll[Long]].get(3) == INPUTS(1).R4[Coll[Long]].get(0),
            OUTPUTS(2).tokens(0)._1 == SELF.tokens(0)._1,
            OUTPUTS(2).tokens(1)._1 == stakedTokenID,
            OUTPUTS(2).tokens(1)._2 == OUTPUTS(2).R4[Coll[Long]].get(3)
        )))
    } else {
    if (stakeStateInput && INPUTS(1).id == SELF.id) { // Compound transaction
        // Stake State, Emission (SELF), Stake*N => Stake State, Emission, Stake*N
        val stakeBoxes = INPUTS.filter({(box: Box) => if (box.tokens.size > 0) box.tokens(0)._1 == stakeTokenID else false})
        val stakeSum = stakeBoxes.fold(0L, {(z: Long, box: Box) => z+box.tokens(1)._2})
        val rewardsSum = stakeSum*SELF.R4[Coll[Long]].get(3)/SELF.R4[Coll[Long]].get(0)
        val remainingTokens = if (SELF.tokens(1)._2 <= rewardsSum) OUTPUTS(1).tokens.size == 1 else (OUTPUTS(1).tokens(1)._1 == stakedTokenID && OUTPUTS(1).tokens(1)._2 >= (SELF.tokens(1)._2 - rewardsSum))
        sigmaProp(allOf(Coll(
             OUTPUTS(1).propositionBytes == SELF.propositionBytes,
             OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
             remainingTokens,
             OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
             OUTPUTS(1).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
             OUTPUTS(1).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2) - stakeBoxes.size,
             OUTPUTS(1).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3)
         )))
    } else {
        sigmaProp(false)
    }
    }
}
""".stripMargin

val emissionContract = ErgoScriptCompiler.compile(
  Map(
    "_stakedTokenID" -> stakedTokenId.tokenId,
    "_stakeStateNFT" -> stakeStateNFT.tokenId,
    "_stakeTokenID" -> stakeTokenId.tokenId,
    "_stakeStateContractHash" -> Base64.getEncoder.encodeToString(
      Blake2b256(stakeStateContract.ergoTree.bytes)
    )
  ),
  emissionScript
)

val stakePoolScript = """
{
    // Stake Pool
    // Registers:
    // 4:0 Long: Emission amount per cycle
    // Assets:
    // 0: Stake Pool NFT
    // 1: Remaining Staked Tokens for future distribution (ErgoPad)

    val stakeStateNFT = _stakeStateNFT
    val stakeStateContract = fromBase64(_stakeStateContractHash)
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == stakeStateContract
    if (stakeStateInput && INPUTS(1).id == SELF.id) { // Emit transaction
        sigmaProp(allOf(Coll(
            //Stake State, Stake Pool (self), Emission => Stake State, Stake Pool, Emission
            OUTPUTS(1).propositionBytes == SELF.propositionBytes,
            OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
            OUTPUTS(1).tokens(1)._1 == SELF.tokens(1)._1,
            OUTPUTS(1).tokens(1)._2 == SELF.tokens(1)._2 + (if (INPUTS(2).tokens.size >= 2) INPUTS(2).tokens(1)._2 else 0L) - SELF.R4[Coll[Long]].get(0),
            OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0)
        )))
    } else {
        sigmaProp(false)
    }
}
""".stripMargin

val stakePoolContract = ErgoScriptCompiler.compile(
  Map(
    "_stakeStateNFT" -> stakeStateNFT.tokenId,
    "_stakeStateContractHash" -> Base64.getEncoder.encodeToString(
      Blake2b256(stakeStateContract.ergoTree.bytes)
    )
  ),
  stakePoolScript
)

val stakeScript = """
{
    // Stake
    // Registers:
    // 4:0 Long: Checkpoint
    // 4:1 Long: Stake time
    // 5: Coll[Byte]: Stake Key ID to be used for unstaking 
    // Assets:
    // 0: Stake Token: 1 token to prove this is a legit stake box
    // 1: Staked Token (ErgoPad): The tokens staked by the user
    
    val stakeStateNFT = _stakeStateNFT
    val emissionNFT = _emissionNFT
    val stakeStateContract = fromBase64(_stakeStateContractHash)
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == stakeStateContract

    if (INPUTS(1).tokens(0)._1 == emissionNFT) { // Compound transaction
        // Stake State, Emission, Stake*N (SELF) => Stake State, Emission, Stake * N   
		    val boxIndex = INPUTS.indexOf(SELF,0)
        val selfReplication = OUTPUTS(boxIndex)
         sigmaProp(allOf(Coll(
             stakeStateInput,
             selfReplication.value == SELF.value,
             selfReplication.propositionBytes == SELF.propositionBytes,
             selfReplication.R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + 1,
			       selfReplication.R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get,
             selfReplication.R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
             selfReplication.tokens(0)._1 == SELF.tokens(0)._1,
             selfReplication.tokens(0)._2 == SELF.tokens(0)._2,
             selfReplication.tokens(1)._1 == SELF.tokens(1)._1,
             selfReplication.tokens(1)._2 == SELF.tokens(1)._2 + (INPUTS(1).R4[Coll[Long]].get(3) * SELF.tokens(1)._2 / INPUTS(1).R4[Coll[Long]].get(0))
         )))
    } else {
    if (INPUTS(1).id == SELF.id) { // Unstake
        val selfReplication = if (OUTPUTS(2).propositionBytes == SELF.propositionBytes) 
                                OUTPUTS(2).R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get &&
                                OUTPUTS(1).tokens(1)._1 == INPUTS(1).R5[Coll[Byte]].get
                              else true
        sigmaProp(stakeStateInput && selfReplication) //Stake state handles logic here to minimize stake box size
    } else {
        sigmaProp(false)
    }
    }
}
""".stripMargin

val stakeContract = ErgoScriptCompiler.compile(
  Map(
    "_stakeStateNFT" -> stakeStateNFT.tokenId,
    "_emissionNFT" -> emissionNFT.tokenId,
    "_stakeStateContractHash" -> Base64.getEncoder.encodeToString(
      Blake2b256(stakeStateContract.ergoTree.bytes)
    )
  ),
  stakeScript
)

///////////////////////////////////////////////////////////////////////////////////
// Wallet initializations                                                        //
///////////////////////////////////////////////////////////////////////////////////

ergopadio.generateUnspentBoxes(
  toSpend = 1000 * nanoergsInErg,
  tokensToSpend = List(
    stakedTokenId -> 40000000000L,
    stakeStateNFT -> 1L,
    stakePoolNFT -> 1L,
    emissionNFT -> 1L,
    stakeTokenId -> 1000000000L
  )
)
ergopadio.printUnspentAssets()
println("-----------")
println(stakeStateNFT)
//Bootstrap

val initStakeStateBox = Box(
  value = minErg,
  tokens = List(
    stakeStateNFT -> 1L,
    stakeTokenId -> 1000000000L
  ),
  registers = Map(
    R4 -> Array[Long](0L,0L,0L,0L,300000L)
  ),
  script = stakeStateContract
)

val initStakePoolBox = Box(
  value = minErg,
  tokens = List(
    stakePoolNFT -> 1L,
    stakedTokenId -> 32100000000L
  ),
  registers = Map(
    R4 -> Array[Long](12000000L)
  ),
  script = stakePoolContract
)

val initEmissionBox = Box(
  value = minErg,
  token = emissionNFT -> 1L,
  registers = Map(
    R4 -> Array[Long](0L,0L,0L,12000000L)
  ),
  script = emissionContract
)

val bootstrapTransaction = Transaction(
  inputs = ergopadio.selectUnspentBoxes(
    toSpend = 3 * minErg + MinTxFee,
    tokensToSpend = List(
      stakeStateNFT -> 1L,
      stakeTokenId -> 1000000000L,
      stakePoolNFT -> 1L,
      stakedTokenId -> 32100000000L,
      emissionNFT -> 1L
    )
  ),
  outputs = List(initStakeStateBox, initStakePoolBox, initEmissionBox),
  fee = MinTxFee,
  sendChangeTo = ergopadio.wallet.getAddress
)

val bootstrapTransactionSigned = ergopadio.wallet.sign(bootstrapTransaction)

// Submit the tx to the simulated blockchain
blockchainSim.send(bootstrapTransactionSigned)
var stakeState = bootstrapTransactionSigned.outputs(0)
var stakePool = bootstrapTransactionSigned.outputs(1)
var emission = bootstrapTransactionSigned.outputs(2)

// stake

stakerA.generateUnspentBoxes(
  toSpend = 10 * nanoergsInErg,
  tokensToSpend = List(stakedTokenId -> 10000L)
)
stakerA.printUnspentAssets()

val newStakeStateBoxA = Box(
  value = stakeState.value,
  tokens = List(
    stakeStateNFT -> 1L,
    stakeTokenId -> (stakeState.additionalTokens(1)._2 - 1L)
  ),
  registers = Map(
    R4 -> Array[Long]((LongArrayConstant
      .unapply(stakeState.additionalRegisters(R4))
      .get(0) + 10000L),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),
      (LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(2) + 1L),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(3),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(4))
  ),
  script = stakeStateContract
)

//Simulate minting new nft
val stakeAKey = blockchainSim.newToken("ErgoPad Stake Key")

val userABox = Box(
  value = minErg,
  token = stakeAKey -> 1L,
  script = contract(stakerA.wallet.getAddress.pubKey)
)

val stakeABox = Box(
  value = minErg,
  tokens = List(
    stakeTokenId -> 1L,
    stakedTokenId -> 10000L
  ),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),
      0L),
    R5 -> userABox.additionalTokens(0)._1
  ),
  script = stakeContract
)

val stakeATransaction = Transaction(
  inputs = List(stakeState) ++ stakerA.selectUnspentBoxes(
    toSpend = minErg + MinTxFee,
    tokensToSpend = List(stakedTokenId -> 10000L)
  ),
  outputs = List(newStakeStateBoxA, stakeABox, userABox),
  fee = MinTxFee,
  sendChangeTo = stakerA.wallet.getAddress
)

val stakeATransactionSigned = stakerA.wallet.sign(stakeATransaction)
blockchainSim.send(stakeATransactionSigned)

stakeState = stakeATransactionSigned.outputs(0)
var stakerABox = stakeATransactionSigned.outputs(1)

println(stakerABox)
println(stakeATransactionSigned.outputs(2))

// stake

stakerB.generateUnspentBoxes(
  toSpend = 10 * nanoergsInErg,
  tokensToSpend = List(stakedTokenId -> 10000L)
)
stakerB.printUnspentAssets()

val newStakeStateBoxB = Box(
  value = stakeState.value,
  tokens = List(
    stakeStateNFT -> 1L,
    stakeTokenId -> (stakeState.additionalTokens(1)._2 - 1L)
  ),
  registers = Map(
    R4 -> Array[Long]((LongArrayConstant
      .unapply(stakeState.additionalRegisters(R4))
      .get(0) + 10000L),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),
      (LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(2) + 1L),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(3),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(4))
  ),
  script = stakeStateContract
)

//Simulate minting new nft
val stakeBKey = blockchainSim.newToken("ErgoPad Stake Key")

val userBBox = Box(
  value = minErg,
  token = stakeBKey -> 1L,
  script = contract(stakerA.wallet.getAddress.pubKey)
)

val stakeBBox = Box(
  value = minErg,
  tokens = List(
    stakeTokenId -> 1L,
    stakedTokenId -> 10000L
  ),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),0L),
    R5 -> userBBox.additionalTokens(0)._1
  ),
  script = stakeContract
)

val stakeBTransaction = Transaction(
  inputs = List(stakeState) ++ stakerB.selectUnspentBoxes(
    toSpend = minErg + MinTxFee,
    tokensToSpend = List(stakedTokenId -> 10000L)
  ),
  outputs = List(newStakeStateBoxB, stakeBBox, userBBox),
  fee = MinTxFee,
  sendChangeTo = stakerB.wallet.getAddress
)

val stakeBTransactionSigned = stakerB.wallet.sign(stakeBTransaction)
blockchainSim.send(stakeBTransactionSigned)

stakeState = stakeBTransactionSigned.outputs(0)
var stakerBBox = stakeBTransactionSigned.outputs(1)

ergopadio.printUnspentAssets()
stakerB.printUnspentAssets()

// Emit
var newStakeState = Box(
  value = stakeState.value,
  tokens = List(
    stakeStateNFT -> 1L,
    stakeTokenId -> (stakeState.additionalTokens(1)._2)
  ),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant
      .unapply(stakeState.additionalRegisters(R4))
      .get(0),
      (LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1) + 1L),
       LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(2),
      (LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(3)+LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(4)),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(4))
  ),
  script = stakeStateContract
)

var newStakePool = Box(
  value = stakePool.value,
  tokens = List(
    stakePoolNFT -> 1L,
    stakedTokenId -> (stakePool.additionalTokens(1)._2 - LongArrayConstant.unapply(stakePool.additionalRegisters(R4)).get(0))
  ),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant.unapply(stakePool.additionalRegisters(R4)).get(0))
  ),
  script = stakePoolContract
)

var newEmission = Box(
  value = emission.value,
  tokens = List(
    emissionNFT -> 1L,
    stakedTokenId -> LongArrayConstant.unapply(stakePool.additionalRegisters(R4)).get(0)
    ),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(0),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(2),
      LongArrayConstant.unapply(stakePool.additionalRegisters(R4)).get(0))
  ),
  script = emissionContract
)

val emitTransaction = Transaction(
  inputs = List(stakeState, stakePool, emission) ++ ergopadio.selectUnspentBoxes(
    toSpend = MinTxFee
  ),
  outputs = List(newStakeState, newStakePool, newEmission),
  fee = MinTxFee,
  sendChangeTo = ergopadio.wallet.getAddress
)

val emitTransactionSigned = ergopadio.wallet.sign(emitTransaction)

// Submit the tx to the simulated blockchain
blockchainSim.send(emitTransactionSigned)
stakeState = emitTransactionSigned.outputs(0)
stakePool = emitTransactionSigned.outputs(1)
emission = emitTransactionSigned.outputs(2)

//Compound
val stakerAReward = stakerABox.additionalTokens(1)._2*LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(3)/LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(0)
var totalAdded = stakerAReward

var newStakerABox = Box(
  value = stakerABox.value,
  tokens = List(
    stakeTokenId -> 1L,
    stakedTokenId -> (stakerABox.additionalTokens(1)._2+stakerAReward)
  ),
  registers = Map(
    R4 -> Array[Long]((LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(1)+1),LongArrayConstant.unapply(stakerABox.additionalRegisters(R4)).get(1)),
    R5 -> userABox.additionalTokens(0)._1
  ),
  script = stakeContract
)

val stakerBReward = stakerBBox.additionalTokens(1)._2*LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(3)/LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(0)
totalAdded = totalAdded + stakerBReward

var newStakerBBox = Box(
  value = stakerBBox.value,
  tokens = List(
    stakeTokenId -> 1L,
    stakedTokenId -> (stakerBBox.additionalTokens(1)._2+stakerBReward)
  ),
  registers = Map(
    R4 -> Array[Long]((LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(1)+1L),LongArrayConstant.unapply(stakerBBox.additionalRegisters(R4)).get(1)),
    R5 -> userBBox.additionalTokens(0)._1
  ),
  script = stakeContract
)

newStakeState = Box(
  value = stakeState.value,
  tokens = List(
    stakeStateNFT -> 1L,
    stakeTokenId -> stakeState.additionalTokens(1)._2
  ),
  registers = Map(
    R4 -> Array[Long]((LongArrayConstant
      .unapply(stakeState.additionalRegisters(R4))
      .get(0) + totalAdded),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(1),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(2),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(3),
      LongArrayConstant.unapply(stakeState.additionalRegisters(R4)).get(4))
  ),
  script = stakeStateContract
)

newEmission = Box(
  value = emission.value,
  tokens = if (emission.additionalTokens(1)._2 - totalAdded > 0) List(emissionNFT -> 1L,stakedTokenId -> (emission.additionalTokens(1)._2 - totalAdded))
           else List(emissionNFT -> 1L),
  registers = Map(
    R4 -> Array[Long](LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(0),
      LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(1),
      (LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(2) - 2L),
      LongArrayConstant.unapply(emission.additionalRegisters(R4)).get(3))
  ),
  script = emissionContract
)

println(stakerAReward)
println(stakerBReward)
println(totalAdded)
println(stakerBBox)
println(newStakerBBox)

val compoundTransaction = Transaction(
  inputs = List(stakeState, emission, stakerABox, stakerBBox) ++ ergopadio.selectUnspentBoxes(
    toSpend = 2*MinTxFee
  ),
  outputs = List(newStakeState, newEmission, newStakerABox, newStakerBBox),
  fee = 2*MinTxFee,
  sendChangeTo = ergopadio.wallet.getAddress
)

val compoundTransactionSigned = ergopadio.wallet.sign(compoundTransaction)

// Submit the tx to the simulated blockchain
blockchainSim.send(compoundTransactionSigned)
stakeState = compoundTransactionSigned.outputs(0)
emission = compoundTransactionSigned.outputs(1)
stakerABox = compoundTransactionSigned.outputs(2)
stakerBBox = compoundTransactionSigned.outputs(3)
}