import { Typography, SvgIcon } from '@mui/material';
import { styled } from '@mui/system';
import AssetModal from './AssetModal';
import { useState } from 'react';

const ERGO_ID = 'ergid';
const SIGUSD_TOKEN_ID =
  '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04';
const SIGRSV_TOKEN_ID =
  '003bd19d0187117f130b62e1bcab0939929ff5c7709f843c5c4dd158949285d0';

const StyledAsset = styled('div')(({ theme }) => ({
  width: '100%',
  display: 'flex',
  alignItems: 'center',
  marginTop: theme.spacing(2),
  paddingBottom: theme.spacing(1),
  cursor: 'pointer',
  // marginBottom: theme.spacing(2),
  // padding: theme.spacing(1),
  // borderRadius: '10px',
  // justifyContent: 'space-between',
  // backgroundColor: `rgba( 255, 255, 255, 0.04)`,
}));

const AssetIcon = styled('img')(() => ({
  width: '50px',
  height: 'auto',
  borderRadius: '12px',
}));

const IconWrapper = styled('div')(() => ({
  width: '50px',
  height: 'auto',
  borderRadius: '12px',
  background: 'rgba(102, 102, 102, 0.3)',
}));

const AssetNameContainer = styled('div')(({ theme }) => ({
  flexGrow: 2,
  flexDirection: 'column',
  justifyContent: 'center',
  paddingLeft: theme.spacing(2),
  paddingRight: theme.spacing(2),
  maxWidth: '240px',
  '& .MuiTypography-root': {
    padding: 2,
  },
}));
const AssetAmountContainer = styled('div')(() => ({
  display: 'flex',
  alignItems: 'center',
  flexDirection: 'column',
  justifyContent: 'center',
}));

const AssetItem = ({ asset, stableDenominator = 'USD', type }) => {
  const [showModal, setShowModal] = useState(false);
  const AssetImage = () => {
    if (asset?.r9) {
      return <AssetIcon src={asset?.r9} />;
    } else {
      return (
        <IconWrapper>
          <SvgIcon fontSize="large"></SvgIcon>
        </IconWrapper>
      );
    }
  };

  return (
    <>
      <StyledAsset className="asset" onClick={() => setShowModal(true)}>
        <AssetImage />
        <AssetNameContainer>
          {/* <Typography>{asset.token}</Typography> */}
          <Typography
            sx={{
              maxWidth: '180px',
              display: 'block',
              overflow: 'hidden',
              whiteSpace: 'nowrap',
              textOverflow: 'ellipsis',
            }}
          >
            {asset.name}
          </Typography>
        </AssetNameContainer>
        {type != 'NFT' && (
          <AssetAmountContainer>
            <Typography>{asset.amount}</Typography>
            {[ERGO_ID, SIGUSD_TOKEN_ID, SIGRSV_TOKEN_ID].includes(asset.id) ? (
              <Typography variant="caption">
                ${asset.id == SIGUSD_TOKEN_ID ? asset.amount : asset.amountUSD} {stableDenominator}
              </Typography>
            ) : null}
          </AssetAmountContainer>
        )}
      </StyledAsset>
      <AssetModal
        key={asset.id + '-modal'}
        open={showModal}
        handleClose={() => setShowModal(false)}
        asset={asset}
      />
    </>
  );
};

export default AssetItem;
