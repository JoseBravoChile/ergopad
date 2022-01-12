import { Typography, Grid, Box, TextField, Button, Container } from '@mui/material';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import FilledInput from '@mui/material/FilledInput';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import FormHelperText from '@mui/material/FormHelperText';
import PageTitle from '@components/PageTitle';
import theme from '../styles/theme';
import axios from 'axios';
import { useWallet } from 'utils/WalletContext'
import { useAddWallet } from 'utils/AddWalletContext'
import { useState, useEffect, forwardRef } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import Snackbar from '@mui/material/Snackbar';
import MuiAlert from '@mui/material/Alert';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import QRCode from "react-qr-code";
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import useMediaQuery from '@mui/material/useMediaQuery';

const Alert = forwardRef(function Alert(props, ref) {
	return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
  });

const initialFormData = Object.freeze({
    wallet: '',
    amount: 0.0,
    currency: 'sigusd'
  });

const initialFormErrors = Object.freeze({
    wallet: false,
    amount: false
});

const initialCheckboxState = Object.freeze({
    legal: false,
    risks: false,
    dao: false
})

const initialSuccessMessageData = Object.freeze({
    ergs: 0.0,
    address: '',
    sigusd: 0.0
})

function friendlyAddress(addr, tot = 13) {
    if (addr === undefined || addr.slice === undefined) return ''
    if (addr.length < 30) return addr
    return addr.slice(0, tot) + '...' + addr.slice(-tot);
}

const defaultOptions = {
    headers: {
        'Content-Type': 'application/json',
    },
};

const Purchase = () => {
    const mediumWidthUp = useMediaQuery((theme) => theme.breakpoints.up('md'));
    // boolean object for each checkbox
    const [checkboxState, setCheckboxState] = useState(initialCheckboxState)

    // set true to disable submit button
    const [buttonDisabled, setbuttonDisabled] = useState(true)

    // loading spinner for submit button
    const [isLoading, setLoading] = useState(false);

    // form error object, all booleans
    const [formErrors, setFormErrors] = useState(initialFormErrors)
    
    const [formData, updateFormData] = useState(initialFormData);

    // open error snackbar 
	const [openError, setOpenError] = useState(false);
    // change error message for error snackbar
	const [errorMessage, setErrorMessage] = useState('Please eliminate form errors and try again')

    const [openSuccessSnackbar, setOpenSuccessSnackbar] = useState(false)
    // change error message for error snackbar
	const [successMessageSnackbar, setSuccessMessageSnackbar] = useState('Copied to Clipboard')

    // open success modal
	const [openSuccess, setOpenSuccess] = useState(false);

    const [successMessageData, setSuccessMessageData] = useState(initialSuccessMessageData)

    const [sigusdAllowed, setSigusdAllowed] = useState(0.0)

    const [alignment, setAlignment] = useState('sigusd');

    const [sigusdApprovalMessage, setSigusdApprovalMessage] = useState('Please enter an Ergo address to see how much sigUSD is approved.')

    const [checkTimeout, setCheckTimeout] = useState(false)

    // helper text for sigvalue
    const [sigHelper, setSigHelper] = useState('')


    const apiCheck = () => {
        axios.get(`${process.env.API_URL}/blockchain/info`, { ...defaultOptions })
            .then(res => {
                console.log(res)
                if (res.data.currentTime_ms > 1641229200000 && !checkboxError) {
                    setbuttonDisabled(false)
                    // console.log('set enabled due to GMT date API call')
                }
            })
            .catch((err) => {
				console.log(err)
            }); 
    }

    useEffect(() => {
        if (!isLoading) {
            apiCheck()
        }
    }, [buttonDisabled])

    const handleCurrencyChange = (e, newAlignment) => {
        if (newAlignment !== null) {
            setAlignment(newAlignment);
            updateFormData({
                ...formData,
                currency: e.target.value
            });
        }
    };

    const { wallet } = useWallet()
    const { setAddWalletOpen } = useAddWallet()
    
    const openWalletAdd = () => {
        setAddWalletOpen(true)
    }

    useEffect(() => {
        if (sigusdAllowed >= 0.0) {
            setSigusdApprovalMessage('This address is approved for ' + sigusdAllowed + ' sigUSD max')
        }
        else if (sigusdAllowed < 0.0 && wallet) {
            setSigusdApprovalMessage('There is a pending transaction, either send the funds or wait for it to time-out to try again. ')
        }
        else if (!wallet) {
            setSigusdApprovalMessage('Please enter an Ergo address to see how much sigUSD is approved.')
        }
    }, [sigusdAllowed])

    const checkWalletApproval = (noSnack) => {
        if (wallet != '') {
            axios.get(`${process.env.API_URL}/blockchain/allowance/${wallet}`)
            .then(res => {
                console.log(res);
                console.log(res.data);
                if (res.data?.message === 'remaining sigusd') {
                    setSigusdAllowed(res.data.sigusd)
                    setCheckTimeout(false)
                    handleChange({target: {name: 'amount', value: ''}})
                }
                else if (res.data?.message === 'pending') {
                    setSigusdAllowed(res.data.sigusd)
                    setCheckTimeout(true)
                    setSigHelper('Please wait for pending transaction to time-out')
                    if (formErrors.amount != true) {
                        setFormErrors({
                            ...formErrors,
                            amount: true
                        });
                    }
                    if (noSnack) {
                        setErrorMessage('Transaction is still pending (it takes 5 minutes)')
                        setOpenError(true)
                    }
                }
            })
            .catch((err) => {
                console.log(err?.response?.data)
            });
        }
    }

    useEffect(() => {
        if (wallet != '') {
            axios.get(`${process.env.API_URL}/blockchain/allowance/${wallet}`)
            .then(res => {
                console.log(res);
                console.log(res.data);
                if (res.data?.message === 'remaining sigusd') {
                    setSigusdAllowed(res.data.sigusd)
                    setFormErrors({
                        ...formErrors,
                        wallet: false
                    });
                    updateFormData({
                        ...formData,
                        wallet: wallet
                    });
                }
                if (res.data?.message === 'not found') {
                    setSigusdAllowed(0.0)
                    setFormErrors({
                        ...formErrors,
                        wallet: true
                    });
                    updateFormData({
                        ...formData,
                        wallet: wallet
                    });
                }
                else if (res.data?.message === 'pending') {
                    setSigusdAllowed(res.data.sigusd)
                    setSigHelper('Please wait for pending transaction to time-out')
                    setFormErrors({
                        ...formErrors,
                        wallet: false,
                        amount: true
                    });
                    updateFormData({
                        ...formData,
                        wallet: wallet
                    });
                    setCheckTimeout(true)
                }
                
            })
            .catch((err) => {
                console.log(err?.response?.data)
            });
        }
        else {
            setFormErrors({
                ...formErrors,
                wallet: true
            });
            setSigusdAllowed(0.0)
        }
    }, [wallet])

    useEffect(() => {
        if (isLoading) {
            setbuttonDisabled(true)
        }
    }, [isLoading])

    const handleChecked = (e) => {
        setCheckboxState({
            ...checkboxState,
            [e.target.name]: e.target.checked
        })
    }

    const { legal, risks, dao } = checkboxState;
    const checkboxError = [legal, risks, dao].filter((v) => v).length !== 3

    useEffect(() => {
        apiCheck()
        if (checkboxError && buttonDisabled != true) {
            setbuttonDisabled(true)
            // console.log('set disabled due to checkbox error')
        }
    }, [checkboxError])

    // snackbar for error reporting
	const handleCloseError = (e, reason) => {
		if (reason === 'clickaway') {
			return;
		}
		setOpenError(false);
	};

    const handleCloseSuccessSnackbar = (e, reason) => {
		if (reason === 'clickaway') {
			return;
		}
		setOpenSuccessSnackbar(false);
	};

    // modal for success message
	const handleCloseSuccess = () => {
		setOpenSuccess(false);
	};

    const copyToClipboard = (text) => {
        setSuccessMessageSnackbar('Copied ' + text + ' to clipboard')
        setOpenSuccessSnackbar(true)
    }

    const handleChange = (e) => {
        if (e.target.value == '' || e.target.value == 0.0) {
            setSigHelper('Please enter the amount you\'d like to invest in sigUSD. ')
			setFormErrors({
				...formErrors,
				[e.target.name]: true
			});
		}
		else {
			setFormErrors({
				...formErrors,
				[e.target.name]: false
			});
		}

        if (e.target.name == 'amount') {
			const sigNumber = Number(e.target.value)
			if (sigNumber <= 20000.0 && sigNumber > 0.0 && sigNumber <= sigusdAllowed) {
				setFormErrors({
					...formErrors,
					amount: false
				});
                updateFormData({
                    ...formData,
                    amount: sigNumber,
                });
			}
			else {
                setSigHelper('Must be a value within your approved amount')
				setFormErrors({
					...formErrors,
					amount: true
				});
			}
		}
        
        // console.log(formErrors)
      };

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true)

		const emptyCheck = Object.values(formData).every(v => (v != '') || (v != 0))
		const errorCheck = Object.values(formErrors).every(v => v === false)

        // console.log(formData)
        // console.log(formErrors)
        // console.log('empty: ' + emptyCheck + ' error: ' + errorCheck)
		
		if (errorCheck && emptyCheck) { 
            console.log(formData)
			axios.post(`${process.env.API_URL}/blockchain/purchase/`, { ...formData })
            .then(res => {
                console.log(res);
                console.log(res.data);
                setLoading(false)

                // modal for success message
				setOpenSuccess(true)
                setSuccessMessageData({
                    ...successMessageData,
                    ergs: res.data.total,
                    address: res.data.smartContract,
                    sigusd: (formData.currency === 'sigusd') ? formData.amount : 0.0
                })
                checkWalletApproval(false)
            })
            .catch((err) => {
                if (err.response?.status) {
                    setErrorMessage('ERROR ' + err.response?.status + ' ' + err.response?.data?.message)
                }
                else {
                    setErrorMessage('ERROR: Network error')
                }
                
                setOpenError(true)
                console.log(err)
                setLoading(false)
            }); 
            // setLoading(false)
		}
		else {
			let updateErrors = {}
			Object.entries(formData).forEach(entry => {
				const [key, value] = entry;
				if (value == '') {
                    if (Object.hasOwn(formErrors, key)){
                        let newEntry = {[key]: true}
                        updateErrors = {...updateErrors, ...newEntry};
                    }
				}
			})

			setFormErrors({
				...formErrors,
				...updateErrors
			})

            // snackbar for error message
			setErrorMessage('Please eliminate form errors and try again')
			setOpenError(true)

            // turn off loading spinner for submit button
			setLoading(false)
		}
    };

  return (
    <>
        <Container maxWidth="lg" sx={{ px: {xs: 2, md: 3 } }}>
		<PageTitle 
			title="Purchase ErgoPad Tokens"
			subtitle="If you are approved for strategic sale whitelist, you can purchase tokens here."
		/>
        </Container>

        <Grid container maxWidth='lg' sx={{ mx: 'auto', flexDirection: 'row-reverse', px: {xs: 2, md: 3 } }}>

            <Grid item md={4} sx={{ pl: { md: 4, xs: 0 } }}>
				<Box sx={{ mt: { md: 0, xs: 4 } }}>
                    <Typography variant="h4" sx={{ fontWeight: '700', lineHeight: '1.2' }}>
                        Details
                    </Typography>
                
                    <Typography variant="p" sx={{ fontSize: '1rem', mb: 3 }}>
                        You must be pre-approved on whitelist to be able to purchase tokens. Add your wallet address to check if you have an allocation available. 
                    </Typography>
				</Box>
			</Grid>

			<Grid item md={8}>
				<Box component="form" noValidate onSubmit={handleSubmit}>
					<Typography variant="h4" sx={{ mb: 3, fontWeight: '700' }}>
						Token Purchase Form
					</Typography>
                    <Typography variant="p" sx={{ fontSize: '1rem', mb: 1 }}>
                        Note: {sigusdApprovalMessage}
                    </Typography>
                    <TextField
                        InputProps={{ disableUnderline: true }}
                        required
                        fullWidth
                        id="sigValue"
                        label="Enter the sigUSD value you are sending"
                        name="amount"
                        variant="filled"
                        sx={{ mb: 3 }}
                        onChange={handleChange}
                        error={formErrors.amount}
                        helperText={formErrors.amount && sigHelper}
                    />

                    {checkTimeout && <Button onClick={checkWalletApproval} variant="outlined" sx={{mt: -2, mb: 3}}>Check if transaction has timed-out</Button>}

                    <Typography variant="p" sx={{ fontSize: '1rem', mb: 1 }}>Select which currency you would like to send: </Typography>
                    <ToggleButtonGroup
                        color="primary"
                        value={alignment}
                        exclusive
                        onChange={handleCurrencyChange}
                        sx={{ mb: 3, mt: 0 }}
                        >
                        <ToggleButton value="sigusd">SigUSD</ToggleButton>
                        <ToggleButton value="erg">Erg</ToggleButton>
                    </ToggleButtonGroup>


                    <FormControl
                        variant="filled" 
                        fullWidth
                        required
                        name="wallet"
                        error={formErrors.wallet}
                    >
                        <InputLabel htmlFor="ergoAddress" sx={{'&.Mui-focused': { color: 'text.secondary'}}}>
                            Ergo Wallet Address
                        </InputLabel>
                        <FilledInput
                            id="ergoAddress"
                            value={wallet}
                            onClick={openWalletAdd}
                            readOnly
                            disableUnderline={true}
                            name="wallet"
                            type="ergoAddress"
                            sx={{ 
                                width: '100%', 
                                border: '1px solid rgba(82,82,90,1)', 
                                borderRadius: '4px', 
                            }}
                        />
                        <FormHelperText>
                            {formErrors.wallet && 'Your address must be approved on the whitelist' }
                        </FormHelperText>
                    </FormControl>

                    <FormControl required error={checkboxError}>
                    <FormGroup sx={{mt: 6 }}>
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={legal} 
                                    onChange={handleChecked} 
                                    name="legal" 
                                />
                            }
                            label="I have confirmed that I am legally entitled to invest in a cryptocurrency project of this nature in the jurisdiction in which I reside" 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={risks} 
                                    onChange={handleChecked} 
                                    name="risks" 
                                />
                            }
                            label="I am aware of the risks involved when investing in a project of this nature. There is always a chance an investment with this level of risk can lose all it's value, and I accept full responsiblity for my decision to invest in this project" 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormControlLabel 
                            control={
                                <Checkbox 
                                    checked={dao} 
                                    onChange={handleChecked} 
                                    name="dao" 
                                />
                            }
                            label="I understand that the funds raised by this project will be controlled by the ErgoPad DAO, which has board members throughout the world. I am aware that this DAO does not fall within the jurisdiction of any one country, and accept the implications therein." 
                            sx={{ color: theme.palette.text.secondary, mb: 3 }} 
                        />
                        <FormHelperText>{checkboxError && 'Please accept the terms before submitting'}</FormHelperText>
                    </FormGroup>
                    </FormControl>

                    <Button
                            type="submit"
                            fullWidth
                            disabled={buttonDisabled}
                            // disabled={true}
                            variant="contained"
                            sx={{ mt: 3, mb: 2 }}
                    >
                        Submit
                    </Button>
                    {isLoading && (
                        <CircularProgress
                            size={24}
                            sx={{
                                position: 'relative',
                                top: '-40px',
                                left: '50%',
                                marginTop: '-9px',
                                marginLeft: '-12px',
                            }}
                        />
                    )}
				</Box>

                <Snackbar open={openError} autoHideDuration={4500} onClose={handleCloseError}>
                    <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
                        {errorMessage}
                    </Alert>
                </Snackbar>
                <Snackbar open={openSuccessSnackbar} autoHideDuration={4500} onClose={handleCloseSuccessSnackbar}>
                    <Alert onClose={handleCloseSuccessSnackbar} severity="success" sx={{ width: '100%' }}>
                        {successMessageSnackbar}
                    </Alert>
                </Snackbar>
                <Dialog
                    open={openSuccess}
                    onClose={handleCloseSuccess}
                    aria-labelledby="alert-dialog-title"
                    aria-describedby="alert-dialog-description"
                    sx={{ textAlign: 'center' }}
                >
                    <DialogTitle id="alert-dialog-title" sx={{ pt: 3 }}>
                        Click on the amount and the address to copy them!
                    </DialogTitle>
                    <DialogContent sx={{ display: 'flex', justifyContent: 'center', flexDirection: 'column', textAlign: 'center' }}>
                        <DialogContentText id="alert-dialog-description">
                            Please send exactly {' '}
                            <Typography onClick={() => {
                                    navigator.clipboard.writeText(successMessageData.ergs)
                                    copyToClipboard(successMessageData.ergs)
                                }
                            } variant="span" sx={{ color: 'text.primary' }}>
                                {successMessageData.ergs} Erg
                            </Typography>
                            {(successMessageData.sigusd > 0.0) && 
                            <>{' '}and{' '}<Typography onClick={() => {
                                navigator.clipboard.writeText(successMessageData.sigusd)
                                copyToClipboard(successMessageData.sigusd)
                            }
                            } variant="span" sx={{ color: 'text.primary' }}>
                                 {successMessageData.sigusd} sigUSD
                            </Typography></>}
                            {' '}to{' '}
                            <Typography onClick={() => {
                                    navigator.clipboard.writeText(successMessageData.address)
                                    copyToClipboard(successMessageData.address)
                                }
                            } variant="span" sx={{ color: 'text.primary' }}>
                                {friendlyAddress(successMessageData.address)}
                            </Typography>
                            {(successMessageData.sigusd > 0.0) && 
                                <>
                                    <Typography variant="p" sx={{ fontSize: '0.9rem', mt: 2, mb: 2 }}>
                                        Note: Yoroi users will not need to add 0.01 erg, it is already done by Yoroi. Other wallet users do need to include that amount with the sigUSD tokens they send.
                                    </Typography>
                                </>
                            }
                        </DialogContentText>
                        <Card sx={{ background: '#fff', width: {xs: '200px', md: '370px'}, margin: '16px auto', display: 'flex', justifyContent: 'center'}}>
                            <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                                <QRCode
                                    size={mediumWidthUp ? 320 : 160}
                                    value={"https://explorer.ergoplatform.com/payment-request?address=" + successMessageData.address +
                                    "&amount=" + successMessageData.ergs}
                                />
                            </CardContent>
                        </Card>
                        {(successMessageData.sigusd > 0.0) && 
                                <>
                                    <Typography variant="p" sx={{ fontSize: '0.9rem', mt: 2, mb: 2 }}>
                                        The QR code will not enter sigUSD values for you, you must enter them manually. 
                                    </Typography>
                                </>
                            }
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseSuccess} autoFocus>
                            Close
                        </Button>
                    </DialogActions>
                </Dialog>

			</Grid>

        </Grid>
    </>
  );
};

export default Purchase;
