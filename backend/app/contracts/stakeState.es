{{
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

      val blockTime = CONTEXT.preHeader.timestamp
      val stakedTokenID = fromBase64("{stakedTokenID}")
      val stakePoolNFT = fromBase64("{stakePoolNFT}")
      val emissionNFT = fromBase64("{emissionNFT}")
      val cycleDuration = SELF.R4[Coll[Long]].get(4)
      val stakeContract = fromBase64("{stakeContractHash}")

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
      if (OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1) {{ // Stake transaction
          // Stake State (SELF), User wallet => Stake State, Stake, Stake Key (User)
          sigmaProp(allOf(Coll(
              selfReplication,
              // Stake State
              OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + OUTPUTS(1).tokens(1)._2,
              OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
              OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2)+1,
              OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
              OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2-1,
              // Stake
              blake2b256(OUTPUTS(1).propositionBytes) == stakeContract,
              OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(1),
              OUTPUTS(1).R4[Coll[Long]].get(1) >= blockTime - 1800000L, //Give half an hour leeway for staking start
              OUTPUTS(1).R5[Coll[Byte]].get == SELF.id,
              OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1,
              OUTPUTS(1).tokens(0)._2 == 1L,
              OUTPUTS(1).tokens(1)._1 == stakedTokenID,
              //Stake key
              OUTPUTS(2).propositionBytes == INPUTS(1).propositionBytes,
              OUTPUTS(2).tokens(0)._1 == OUTPUTS(1).R5[Coll[Byte]].get,
              OUTPUTS(2).tokens(0)._2 == 1L
          )))
      }} else {{
      if (INPUTS(1).tokens(0)._1 == stakePoolNFT && INPUTS.size >= 3) {{ // Emit transaction
           // Stake State (SELF), Stake Pool, Emission => Stake State, Stake Pool, Emission
           sigmaProp(allOf(Coll(
               selfReplication,
               //Emission INPUT
               INPUTS(2).tokens(0)._1 == emissionNFT,
               INPUTS(2).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1) - 1L,
               INPUTS(2).R4[Coll[Long]].get(2) == 0L,
               //Stake State
               OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
               OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1) + 1L,
               OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
               OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3) + SELF.R4[Coll[Long]].get(4),
               OUTPUTS(0).R4[Coll[Long]].get(3) < blockTime,
               OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
           )))
      }} else {{
      if (INPUTS(1).tokens(0)._1 == emissionNFT) {{ // Compound transaction
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
       }} else {{
       if (SELF.R4[Coll[Long]].get(0) > OUTPUTS(0).R4[Coll[Long]].get(0) && INPUTS.size >= 3) {{ // Unstake
           // Stake State (SELF), Stake, Stake Key Box => Stake State, User Wallet, Stake (optional for partial unstake)
           val remaining = if (OUTPUTS(2).propositionBytes == INPUTS(1).propositionBytes)
                            INPUTS(1).tokens(1)._2 - OUTPUTS(1).tokens(0)._2
                           else
                            0L
           val stakeKey = INPUTS(2).tokens.exists({{(token: (Coll[Byte],Long)) => token._1 == INPUTS(1).R5[Coll[Byte]].get}})
           val unstaked = INPUTS(1).tokens(1)._2 - remaining
           val timeInWeeks = (blockTime - INPUTS(1).R4[Coll[Long]].get(1))/1000/3600/24/7
           val penalty =  if (timeInWeeks > 8) 0L else
                           if (timeInWeeks > 6) unstaked*5/100 else
                           if (timeInWeeks > 4) unstaked*125/1000 else
                           if (timeInWeeks > 2) unstaked*20/100 else
                           unstaked*25/100
           sigmaProp(allOf(Coll(
               selfReplication,
               stakeKey,
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
       }} else {{
           sigmaProp(false)
       }}
       }}
       }}
      }}
  }}