import { Typography, Grid, Box, TextField, Button, Container } from '@mui/material';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
// import FormHelperText from '@mui/material/FormHelperText';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import FormControl from '@mui/material/FormControl';
import FilledInput from '@mui/material/FilledInput';
import FormHelperText from '@mui/material/FormHelperText';
import Select from '@mui/material/Select';
import PageTitle from '@components/PageTitle';
import theme from '../styles/theme';
import MuiNextLink from '@components/MuiNextLink'
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

const Alert = forwardRef(function Alert(props, ref) {
	return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
  });
  

const initialFormData = Object.freeze({
    name: '',
    email: '',
    sigValue: '',
    ergoAddress: '',
    chatHandle: '',
    chatPlatform: '',
  });

const initialFormErrors = Object.freeze({
	name: false,
    email: false,
    sigValue: false,
    ergoAddress: false,
    chatHandle: false,
    chatPlatform: false,
})

const initialCheckboxState = Object.freeze({
    legal: false,
    risks: false,
    dao: false
})

const defaultOptions = {
    headers: {
        'Content-Type': 'application/json',
    },
};

const emailRegex = /\S+@\S+\.\S+/;

const Whitelist = () => {
    // boolean object for each checkbox
    const [checkboxState, setCheckboxState] = useState(initialCheckboxState)

    // set true to disable submit button
    const [buttonDisabled, setbuttonDisabled] = useState(true)
    
    // form error object, all booleans
    const [formErrors, setFormErrors] = useState(initialFormErrors)

    // form data is all strings
    const [formData, updateFormData] = useState(initialFormData);

    // loading spinner for submit button
    const [isLoading, setLoading] = useState(false);

    // open error snackbar 
	const [openError, setOpenError] = useState(false);

    // open success modal
	const [openSuccess, setOpenSuccess] = useState(false);

    // change error message for error snackbar
	const [errorMessage, setErrorMessage] = useState('Please eliminate form errors and try again')

    // disable form after API endpoint reports max submissions hit
    const [soldOut, setSoldOut] = useState(false)

    const [timeLock, setTimeLock] = useState(true)

    // brings wallet data from AddWallet modal component. Will load from localStorage if wallet is set
    const { wallet } = useWallet()

    // opens the modal to set wallet into localStorage
    const { setAddWalletOpen } = useAddWallet()

    const openWalletAdd = () => {
        setAddWalletOpen(true)
    }

    const apiCheck = () => {
        axios.get(`${process.env.API_URL}/util/whitelist`, { ...defaultOptions })
            .then(res => {
                console.log(res)
                const maxSale = 550000
                // console.log(res)
                if (res.data.gmt > 1640538000 && !checkboxError && !soldOut) {
                    setbuttonDisabled(false)
                    setTimeLock(false)
                    // console.log('set enabled due to GMT date API call')
                }
                if (res.data.qty > maxSale && !soldOut) {
                    setbuttonDisabled(true)
                    // console.log('set disabled due to max applicants')
                    setSoldOut(true)
                }
                else if (res.data.qty < maxSale) {
                    // ('not sold out')
                    setSoldOut(false)
                }
            })
            .catch((err) => {
				console.log(err)
            }); 
    }

    useEffect(() => {
        apiCheck()
    }, [buttonDisabled])

    useEffect(() => {
        updateFormData({
            ...formData,
            ergoAddress: wallet
          });
		if (wallet) {
			setFormErrors({
				...formErrors,
				ergoAddress: false
			});
		}
		else {
			setFormErrors({
				...formErrors,
				ergoAddress: true
			});
		}
    }, [wallet])

    useEffect(() => {
        if (isLoading) {
            // console.log('set disabled due to isLoading')
            setbuttonDisabled(true)
        }
    }, [isLoading])

    const handleChange = (e) => {
		if (e.target.value == '') {
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
		
		if (e.target.name == 'email') {
            if (emailRegex.test(e.target.value)) {
                setFormErrors({
					...formErrors,
					email: false
				});
            }
            else {
                setFormErrors({
					...formErrors,
					email: true
				});
            }
        }

		if (e.target.name == 'sigValue') {
			const sigNumber = Number(e.target.value)
			if (sigNumber <= 20000 && sigNumber > 0 ) {
				setFormErrors({
					...formErrors,
					sigValue: false
				});
			}
			else {
				setFormErrors({
					...formErrors,
					sigValue: true
				});
			}
		}

        updateFormData({
          ...formData,
            
          // Trimming any whitespace
          [e.target.name]: e.target.value.trim()
        });

        console.log(formData)
      };

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
	const handleCloseError = (event, reason) => {
		if (reason === 'clickaway') {
			return;
		}
		setOpenError(false);
	};

    // modal for success message
	const handleCloseSuccess = () => {
		setOpenSuccess(false);
	};

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true)

		const emptyCheck = Object.values(formData).every(v => v != '')
		const errorCheck = Object.values(formErrors).every(v => v === false)

        const form = {
            name: formData.name,
            email: formData.email,
            sigValue: formData.sigValue,
            ergoAddress: formData.ergoAddress,
            chatHandle: formData.chatHandle,
            chatPlatform: formData.chatPlatform,
            socialHandle: formData.socialHandle,
            socialPlatform: formData.socialPlatform,
        }

		if (errorCheck && emptyCheck) { 
			axios.post(`${process.env.API_URL}/util/whitelist`, { ...form })
            .then(res => {
                console.log(res);
                console.log(res.data);
                setLoading(false)

                // modal for success message
				setOpenSuccess(true)
            })
            .catch((err) => {
                // snackbar for error message
				setErrorMessage('ERROR ' + err.response.status + ' ' + err.response.data.message)
                setOpenError(true)
                console.log(err.response.data)
                setLoading(false)
            }); 
		}
		else {
			let updateErrors = {}
			Object.entries(formData).forEach(entry => {
				const [key, value] = entry;
				if (value == '') {
					let newEntry = {[key]: true}
					updateErrors = {...updateErrors, ...newEntry};
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
			title="Pre-Sale Whitelist"
			subtitle="Apply here to be whitelisted for the ErgoPad pre-sale. It is capped at $20000 sigUSD per investor."
			// main={true}
		/>
        </Container>

        <Grid container maxWidth='lg' sx={{ mx: 'auto', flexDirection: 'row-reverse', px: {xs: 2, md: 3 } }}>

            <Grid item md={4} sx={{ pl: { md: 4, xs: 0 } }}>
				<Box sx={{ mt: { md: 0, xs: 4 } }}>
					<Typography variant="h4" sx={{ fontWeight: '700', lineHeight: '1.2' }}>
						Join the discussion
					</Typography>
				
					<Typography variant="p" sx={{ fontSize: '1rem', mb: 3 }}>
                        You must be in one of the two chatrooms to be eligible for whitelist. 
					</Typography>

					<Box>
						<a href="https://t.me/ergopad_chat" target="_blank" rel="noreferrer">
							<Button 
							variant="contained"
							sx={{
								color: '#fff',
								fontSize: '1rem',
								py: '0.6rem',
								px: '1.2rem',
								mr: '1.7rem',
								textTransform: 'none',
								backgroundColor: theme.palette.primary.main,
								'&:hover': {
								backgroundColor: theme.palette.primary.hover,
								boxShadow: 'none',
								},
								'&:active': {
								backgroundColor: theme.palette.primary.active,
								},
							}}
							>
							Telegram
							</Button>
						</a>

						<a href="https://discord.gg/E8cHp6ThuZ" target="_blank" rel="noreferrer">
							<Button 
							variant="contained"
							sx={{
								color: '#fff',
								fontSize: '1rem',
								py: '0.6rem',
								px: '1.2rem',
								textTransform: 'none',
								backgroundColor: theme.palette.secondary.main,
								'&:hover': {
								backgroundColor: theme.palette.secondary.hover,
								boxShadow: 'none',
								},
								'&:active': {
								backgroundColor: theme.palette.secondary.active,
								},

							}}
							>
							Discord
							</Button>
						</a>
					</Box>
				</Box>

                <Typography variant="h4" sx={{ fontWeight: '700', lineHeight: '1.2', mt: 6 }}>
                    Details
                </Typography>
            
                <Typography variant="p" sx={{ fontSize: '1rem', mb: 3 }}>
                    Pre-sale is capped at $20k sigUSD investment per person. You will receive an email whether your are accepted or if we need further details. 
                </Typography>

                <Typography variant="p" sx={{ fontSize: '1rem', mb: 3 }}>
                    You will be sent a URL to go to on January 20th when pre-sale is live and instructions will be provided. Please follow the instructions carefully to lock your tokens in the vesting smart-contract. 
                </Typography>
			</Grid>


			<Grid item md={8}>
				<Box component="form" noValidate onSubmit={handleSubmit}>
					<Typography variant="h4" sx={{ mb: 4, fontWeight: '700' }}>
						Application Form
					</Typography>
					<Grid container spacing={2}>
					<Grid item xs={12} sm={6}>
						<TextField
                            InputProps={{ disableUnderline: true }}
                            required
                            fullWidth
                            id="name"
                            label="Your Name"
                            name="name"
                            variant="filled"
                            onChange={handleChange}
							error={formErrors.name}
							helperText={formErrors.name && 'Enter your name'}
						/>
					</Grid>
					<Grid item xs={12} sm={6}>
						<TextField
                            InputProps={{ disableUnderline: true }}
                            fullWidth
                            required
                            name="email"
                            label="Your Email"
                            error={formErrors.email}
                            id="email"
                            variant="filled"
                            helperText={formErrors.email && 'Please enter a valid email address'}
                            onChange={handleChange}
						/>
					</Grid>
                    <Grid item xs={12}>
                        <Typography color="text.secondary">Enter how much in sigUSD you&apos;d like to invest. You can send Erg or SigUSD on the sale date. </Typography>
						<TextField
                            InputProps={{ disableUnderline: true }}
                            required
                            fullWidth
                            id="sigValue"
                            label="How much would you like to invest in SigUSD value"
                            name="sigValue"
                            variant="filled"
                            helperText={formErrors.sigValue && 'Please enter between 1 and 20000 sigUSD'}
                            onChange={handleChange}
							error={formErrors.sigValue}
						/>
					</Grid>
					<Grid item xs={12}>
                    <FormControl
                        variant="filled" 
                        fullWidth
                        required
						error={formErrors.ergoAddress}
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
                            name="ergoAddress"
                            
                            sx={{ 
                                width: '100%', 
                                border: '1px solid rgba(82,82,90,1)', 
                                borderRadius: '4px', 
                            }}
                        />
                        <FormHelperText>
                            Your address will be pre-approved on the whitelist
                        </FormHelperText>
                    </FormControl>
					</Grid>

                    <Grid item xs={12}>
                        <Typography sx={{ color: theme.palette.text.secondary, mt: 3 }}>
                            Join us on either <MuiNextLink href="http://t.me/ergopad" target="_blank" rel="noreferrer">Telegram</MuiNextLink> or <MuiNextLink href="https://discord.gg/E8cHp6ThuZ" target="_blank" rel="noreferrer">Discord</MuiNextLink> to verify for whitelist. Enter your handle below and select which chatroom you&apos;re in.
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
						<TextField
                            InputProps={{ disableUnderline: true }}
                            required
                            fullWidth
                            id="chatHandle"
                            label="Your TG or Discord Handle"
                            name="chatHandle"
                            error={formErrors.chatHandle}
							helperText={formErrors.chatHandle && 'Please enter your handle'}
                            variant="filled"
                            onChange={handleChange}
						/>
					</Grid>
                     <Grid item xs={12} sm={6}>
                        <FormControl variant="filled" error={formErrors.chatPlatform} required sx={{ minWidth: '100%', }}>
                            <InputLabel id="chatPlatform" sx={{ '&.Mui-focused': { color: theme.palette.text.secondary } }}>Select Platform</InputLabel>
                            <Select
                                disableUnderline={true}
                                id="chatPlatform"
                                name="chatPlatform"
                                value={formData.chatPlatform}
                                variant="filled"
                                onChange={handleChange}
                                sx={{
                                    border: `1px solid rgba(82,82,90,1)`,
                                    borderRadius: '4px',
                                }}
                            >
                                <MenuItem value="telegram">Telegram</MenuItem>
                                <MenuItem value="discord">Discord</MenuItem>
                            </Select>
							<FormHelperText>{formErrors.chatPlatform && 'Please select the platform'}</FormHelperText>
                        </FormControl>
						
                    </Grid> 

					
                    
					</Grid>
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


                    <Box sx={{position: 'relative'}}>
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
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    marginTop: '-9px',
                                    marginLeft: '-12px',
                                }}
                            />
                            )}

                    </Box>
                    <Typography sx={{ color: theme.palette.text.secondary }}>{soldOut && 'We apologize for the inconvenience, the pre-sale round is sold out'}</Typography>
                    <Typography sx={{ color: theme.palette.text.secondary }}>{timeLock && 'Please wait until 17:00 UTC, December 26th. If the submit button is not active after this time and all check-boxes are checked, refresh the page to activate the form.'}</Typography>
					<Snackbar open={openError} autoHideDuration={6000} onClose={handleCloseError}>
						<Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
							{errorMessage}
						</Alert>
					</Snackbar>
					<Dialog
						open={openSuccess}
						onClose={handleCloseSuccess}
						aria-labelledby="alert-dialog-title"
						aria-describedby="alert-dialog-description"
					>
						<DialogTitle id="alert-dialog-title">
							{"Form submitted"}
						</DialogTitle>
						<DialogContent>
							<DialogContentText id="alert-dialog-description">
								We have received your application and will get back to you shortly. If approved, instructions will be sent on how to secure your tokens on January 3rd. Thanks a lot for your support!
							</DialogContentText>
						</DialogContent>
						<DialogActions>
							<MuiNextLink href="/">
								<Button onClick={handleCloseSuccess} autoFocus>
									Go Home
								</Button>
							</MuiNextLink>
						</DialogActions>
					</Dialog>

					
				</Box>
			</Grid>

        </Grid>
    </>
  );
};

export default Whitelist;
