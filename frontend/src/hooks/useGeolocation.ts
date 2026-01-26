import { useState, useEffect } from 'react'

interface GeolocationState {
    coordinates: {
        latitude: number
        longitude: number
    } | null
    error: string | null
    loading: boolean
}

interface GeolocationOptions {
    enableHighAccuracy?: boolean
    timeout?: number
    maximumAge?: number
}

export const useGeolocation = (options: GeolocationOptions = {}) => {
    const [state, setState] = useState<GeolocationState>({
        coordinates: null,
        error: null,
        loading: false
    })

    const {
        enableHighAccuracy = false,
        timeout = 5000,
        maximumAge = 0
    } = options

    const getCurrentPosition = () => {
        if (!navigator.geolocation) {
            setState(prev => ({
                ...prev,
                error: 'Geolocation is not supported by this browser',
                loading: false
            }))
            return
        }

        setState(prev => ({ ...prev, loading: true, error: null }))

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setState({
                    coordinates: {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    },
                    error: null,
                    loading: false
                })
            },
            (error) => {
                let errorMessage = 'Failed to get location'

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied by user'
                        break
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable'
                        break
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out'
                        break
                }

                setState({
                    coordinates: null,
                    error: errorMessage,
                    loading: false
                })
            },
            {
                enableHighAccuracy,
                timeout,
                maximumAge
            }
        )
    }

    const clearLocation = () => {
        setState({
            coordinates: null,
            error: null,
            loading: false
        })
    }

    return {
        ...state,
        getCurrentPosition,
        clearLocation,
        isSupported: !!navigator.geolocation
    }
}