import React, { useState, useEffect } from 'react'
import {
    TextField,
    Box,
    Button,
    Typography,
    Alert,
    CircularProgress,
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
    const [isGettingLocation, setIsGettingLocation] = useState(false)
    const [locationError, setLocationError] = useState<string | null>(null)

    useEffect(() => {
        if (location?.address) {
            setAddress(location.address)
        }
    }, [location])

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
                    // Try to get address from coordinates using reverse geocoding
                    // For now, we'll use a simple format
                    const locationData: LocationData = {
                        type: 'Point',
                        coordinates: [longitude, latitude],
                        address: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
                    }

                    // In a real implementation, you would use a geocoding service
                    // to convert coordinates to a human-readable address
                    setAddress(locationData.address || '')
                    onChange(locationData)
                } catch (error) {
                    console.error('Error getting address:', error)
                    const locationData: LocationData = {
                        type: 'Point',
                        coordinates: [longitude, latitude],
                        address: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
                    }
                    setAddress(locationData.address || '')
                    onChange(locationData)
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

    const handleAddressChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newAddress = event.target.value
        setAddress(newAddress)

        if (newAddress.trim()) {
            // For now, create a basic location object
            // In a real implementation, you would geocode the address
            const locationData: LocationData = {
                type: 'Point',
                coordinates: [0, 0], // Default coordinates
                address: newAddress,
            }
            onChange(locationData)
        }
    }

    return (
        <Box>
            <TextField
                fullWidth
                label={t('auth.location')}
                value={address}
                onChange={handleAddressChange}
                required={required}
                error={error}
                helperText={helperText}
                placeholder="Enter your city, state or full address"
                InputProps={{
                    startAdornment: <LocationOn sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
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
                    {isGettingLocation ? 'Getting Location...' : 'Use Current Location'}
                </Button>

                <Typography variant="body2" color="text.secondary">
                    or enter manually above
                </Typography>
            </Box>

            {locationError && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                    {locationError}
                </Alert>
            )}

            {location && location.coordinates[0] !== 0 && location.coordinates[1] !== 0 && (
                <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        <strong>Coordinates:</strong> {location.coordinates[1].toFixed(6)}, {location.coordinates[0].toFixed(6)}
                    </Typography>
                </Box>
            )}
        </Box>
    )
}