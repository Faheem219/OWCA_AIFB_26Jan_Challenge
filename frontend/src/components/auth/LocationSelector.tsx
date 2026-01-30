import React, { useState, useEffect } from 'react'
import {
    TextField,
    Box,
    Button,
    Typography,
    Alert,
    CircularProgress,
    Grid,
} from '@mui/material'
import { LocationOn, MyLocation } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { LocationData } from '../../types'

interface LocationSelectorProps {
    location: LocationData | null
    onChange: (location: LocationData) => void
    required?: boolean
    error?: boolean
    helperText?: string
}

export const LocationSelector: React.FC<LocationSelectorProps> = ({
    location,
    onChange,
    required = false,
    error = false,
    helperText,
}) => {
    const { t } = useTranslation()
    const [address, setAddress] = useState(location?.address || '')
    const [city, setCity] = useState(location?.city || '')
    const [state, setState] = useState(location?.state || '')
    const [pincode, setPincode] = useState(location?.pincode || '')
    const [isGettingLocation, setIsGettingLocation] = useState(false)
    const [locationError, setLocationError] = useState<string | null>(null)

    useEffect(() => {
        if (location) {
            if (location.address) setAddress(location.address)
            if (location.city) setCity(location.city)
            if (location.state) setState(location.state)
            if (location.pincode) setPincode(location.pincode)
        }
    }, [location])

    const updateLocation = (updates: Partial<{ address: string; city: string; state: string; pincode: string; coordinates: [number, number] }>) => {
        const newAddress = updates.address !== undefined ? updates.address : address
        const newCity = updates.city !== undefined ? updates.city : city
        const newState = updates.state !== undefined ? updates.state : state
        const newPincode = updates.pincode !== undefined ? updates.pincode : pincode
        const newCoordinates = updates.coordinates || location?.coordinates || [0, 0]

        const locationData: LocationData = {
            type: 'Point',
            coordinates: newCoordinates as [number, number],
            address: newAddress || `${newCity}, ${newState}`,
            city: newCity,
            state: newState,
            pincode: newPincode,
        }
        onChange(locationData)
    }

    const getCurrentLocation = () => {
        setIsGettingLocation(true)
        setLocationError(null)

        if (!navigator.geolocation) {
            setLocationError('Geolocation is not supported by this browser')
            setIsGettingLocation(false)
            return
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords

                try {
                    updateLocation({
                        coordinates: [longitude, latitude],
                        address: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
                    })
                } catch (error) {
                    console.error('Error getting address:', error)
                    updateLocation({
                        coordinates: [longitude, latitude],
                        address: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
                    })
                }

                setIsGettingLocation(false)
            },
            (error) => {
                console.error('Error getting location:', error)
                setLocationError('Unable to get your location. Please enter manually.')
                setIsGettingLocation(false)
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000, // 5 minutes
            }
        )
    }

    return (
        <Box>
            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label={t('auth.city') || 'City'}
                        value={city}
                        onChange={(e) => {
                            setCity(e.target.value)
                            updateLocation({ city: e.target.value })
                        }}
                        required={required}
                        error={error && !city}
                        placeholder="Enter your city"
                    />
                </Grid>
                <Grid item xs={12} sm={6}>
                    <TextField
                        fullWidth
                        label={t('auth.state') || 'State'}
                        value={state}
                        onChange={(e) => {
                            setState(e.target.value)
                            updateLocation({ state: e.target.value })
                        }}
                        required={required}
                        error={error && !state}
                        placeholder="Enter your state"
                    />
                </Grid>
                <Grid item xs={12} sm={6}>
                    <TextField
                        fullWidth
                        label={t('auth.pincode') || 'Pincode'}
                        value={pincode}
                        onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '').slice(0, 6)
                            setPincode(value)
                            updateLocation({ pincode: value })
                        }}
                        required={required}
                        error={error && (!pincode || pincode.length !== 6)}
                        helperText={pincode && pincode.length !== 6 ? 'Pincode must be 6 digits' : helperText}
                        placeholder="6-digit pincode"
                        inputProps={{ maxLength: 6 }}
                    />
                </Grid>
                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label={t('auth.address') || 'Full Address (Optional)'}
                        value={address}
                        onChange={(e) => {
                            setAddress(e.target.value)
                            updateLocation({ address: e.target.value })
                        }}
                        placeholder="Street address, area, landmark"
                        InputProps={{
                            startAdornment: <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />,
                        }}
                    />
                </Grid>
            </Grid>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2, mb: 2 }}>
                <Button
                    variant="outlined"
                    size="small"
                    startIcon={
                        isGettingLocation ? (
                            <CircularProgress size={16} />
                        ) : (
                            <MyLocation />
                        )
                    }
                    onClick={getCurrentLocation}
                    disabled={isGettingLocation}
                >
                    {isGettingLocation ? 'Getting Location...' : 'Use GPS Coordinates'}
                </Button>
            </Box>

            {locationError && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                    {locationError}
                </Alert>
            )}

            {location && location.coordinates && location.coordinates[0] !== 0 && location.coordinates[1] !== 0 && (
                <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        <strong>GPS Coordinates:</strong> {location.coordinates[1].toFixed(6)}, {location.coordinates[0].toFixed(6)}
                    </Typography>
                </Box>
            )}
        </Box>
    )
}