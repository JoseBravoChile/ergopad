import {
  Typography,
  Modal,
  Box,
  Paper,
  Accordion,
  AccordionDetails,
  AccordionSummary,
} from '@mui/material';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Image from 'next/image'

const style = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '50vw',
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  maxHeight: '80vh',
  overflowY: 'scroll',
};

const flattenJSON = (jsonData) => {
  const _flattenJSON = (obj = {}, res = {}) => {
    Object.keys(obj).forEach((key) => {
      if (typeof obj[key] !== 'object') {
        res[key] = obj[key];
      } else {
        _flattenJSON(obj[key], res);
      }
    });
    return res;
  };
  return _flattenJSON(jsonData);
};

const parseDescription = (description) => {
  try {
    return flattenJSON(JSON.parse(description));
  } catch (e) {
    try {
      // parse error some descriptions have unicode escape characters as the first character
      return flattenJSON(JSON.parse(description.slice(1)));
    } catch (e) {
      // description is a string
      return { Description: description ? description : '' };
    }
  }
};

const AssetModal = ({ open, handleClose, asset }) => {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.up('md'));
  const metadata = parseDescription(asset?.description);

  return (
    <Modal
      keepMounted
      open={open}
      onClose={handleClose}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      <Box sx={matches ? style : { ...style, width: '85vw' }}>
        <Typography id="modal-modal-title" variant="h6" component="h2">
          {asset?.name}
        </Typography>
        <Typography
          id="modal-modal-description"
          sx={{ mt: 2, fontSize: '0.8rem' }}
        >
          <pre>
            <strong>Token ID:</strong> {asset?.id}
          </pre>
          <pre>
            <strong>ch:</strong> {asset?.ch}
          </pre>
          <pre>
            <strong>Token:</strong> {asset?.token}
          </pre>
          <pre>
            <strong>Amount:</strong> {asset?.amount}
          </pre>
          <Accordion>
            <AccordionSummary>
              <strong>Expand for Description</strong>
            </AccordionSummary>
            <AccordionDetails sx={{ overflowWrap: 'break-word' }}>
              
              {Object.keys(metadata)
                .filter((key) => !key.match(/^[0-9]+$/))
                .map((key) => (
                  <>
                  
                  <Typography sx={{ fontSize: '0.9rem', mb: 1 }}>
                    <strong>
                      {key.charAt(0).toUpperCase() + key.slice(1)}:
                    </strong>{' '}
                    {metadata[key]}
                  </Typography>
                  
                  </>
                ))}
                
            </AccordionDetails>
          </Accordion>
        </Typography>
        {asset?.r9 ? (
          <Paper variant="outlined" sx={{ mt: 5 }}>
            <img width="100%" src={asset?.r9} alt={asset?.name} />
          </Paper>
        ) : null}
      </Box>
    </Modal>
  );
};

export default AssetModal;
