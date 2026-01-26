/**
 * Progressive Web App utilities for service worker registration and management.
 */

import { Workbox } from 'workbox-window'

let wb: Workbox | null = null

/**
 * Register service worker for PWA functionality
 */
export const registerSW = () => {
    if ('serviceWorker' in navigator) {
        wb = new Workbox('/sw.js')

        // Add event listeners for service worker lifecycle events
        wb.addEventListener('installed', (event) => {
            console.log('Service worker installed:', event)

            if (event.isUpdate) {
                // Show update available notification
                showUpdateAvailableNotification()
            }
        })

        wb.addEventListener('waiting', (event) => {
            console.log('Service worker waiting:', event)
            showUpdateAvailableNotification()
        })

        wb.addEventListener('controlling', (event) => {
            console.log('Service worker controlling:', event)
            // Reload the page to ensure all resources are served by the new service worker
            window.location.reload()
        })

        wb.addEventListener('activated', (event) => {
            console.log('Service worker activated:', event)
        })

        // Register the service worker
        wb.register()
            .then((registration) => {
                console.log('Service worker registered successfully:', registration)
            })
            .catch((error) => {
                console.error('Service worker registration failed:', error)
            })
    } else {
        console.warn('Service workers are not supported in this browser')
    }
}

/**
 * Update service worker to the latest version
 */
export const updateSW = () => {
    if (wb) {
        wb.messageSkipWaiting()
    }
}

/**
 * Show notification when app update is available
 */
const showUpdateAvailableNotification = () => {
    // Create a custom event that components can listen to
    const event = new CustomEvent('sw-update-available', {
        detail: {
            message: 'A new version of the app is available. Click to update.',
            action: updateSW
        }
    })

    window.dispatchEvent(event)
}

/**
 * Check if the app is running as a PWA
 */
export const isPWA = (): boolean => {
    return window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true ||
        document.referrer.includes('android-app://')
}

/**
 * Check if the app can be installed as a PWA
 */
export const canInstallPWA = (): boolean => {
    return 'beforeinstallprompt' in window
}

/**
 * Prompt user to install the PWA
 */
export const promptPWAInstall = async (): Promise<boolean> => {
    const deferredPrompt = (window as any).deferredPrompt

    if (!deferredPrompt) {
        return false
    }

    try {
        // Show the install prompt
        deferredPrompt.prompt()

        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice

            // Clear the deferred prompt
            ; (window as any).deferredPrompt = null

        return outcome === 'accepted'
    } catch (error) {
        console.error('Error prompting PWA install:', error)
        return false
    }
}

/**
 * Get PWA installation status
 */
export const getPWAInstallStatus = () => {
    return {
        isInstalled: isPWA(),
        canInstall: canInstallPWA(),
        isSupported: 'serviceWorker' in navigator
    }
}

/**
 * Handle PWA install prompt event
 */
export const handlePWAInstallPrompt = () => {
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault()

            // Store the event so it can be triggered later
            ; (window as any).deferredPrompt = e

        // Dispatch custom event that components can listen to
        const event = new CustomEvent('pwa-install-available', {
            detail: {
                prompt: promptPWAInstall
            }
        })

        window.dispatchEvent(event)
    })

    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed')

        // Dispatch custom event
        const event = new CustomEvent('pwa-installed')
        window.dispatchEvent(event)

            // Clear the deferred prompt
            ; (window as any).deferredPrompt = null
    })
}

/**
 * Initialize PWA functionality
 */
export const initializePWA = () => {
    registerSW()
    handlePWAInstallPrompt()
}

/**
 * Check if the device is online
 */
export const isOnline = (): boolean => {
    return navigator.onLine
}

/**
 * Add online/offline event listeners
 */
export const addNetworkListeners = (
    onOnline: () => void,
    onOffline: () => void
) => {
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)

    // Return cleanup function
    return () => {
        window.removeEventListener('online', onOnline)
        window.removeEventListener('offline', onOffline)
    }
}

/**
 * Get network information (if supported)
 */
export const getNetworkInfo = () => {
    const connection = (navigator as any).connection ||
        (navigator as any).mozConnection ||
        (navigator as any).webkitConnection

    if (connection) {
        return {
            effectiveType: connection.effectiveType,
            downlink: connection.downlink,
            rtt: connection.rtt,
            saveData: connection.saveData
        }
    }

    return null
}

/**
 * Check if the user is on a slow connection
 */
export const isSlowConnection = (): boolean => {
    const networkInfo = getNetworkInfo()

    if (networkInfo) {
        return networkInfo.effectiveType === '2g' ||
            networkInfo.effectiveType === 'slow-2g' ||
            networkInfo.saveData === true
    }

    return false
}