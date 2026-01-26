import { createTheme } from '@mui/material/styles'

// Define custom color palette for Indian marketplace theme
const palette = {
    primary: {
        main: '#2e7d32', // Green representing agriculture and growth
        light: '#60ad5e',
        dark: '#005005',
        contrastText: '#ffffff',
    },
    secondary: {
        main: '#ff9800', // Orange representing energy and commerce
        light: '#ffb74d',
        dark: '#f57c00',
        contrastText: '#000000',
    },
    success: {
        main: '#4caf50',
        light: '#81c784',
        dark: '#388e3c',
    },
    warning: {
        main: '#ff9800',
        light: '#ffb74d',
        dark: '#f57c00',
    },
    error: {
        main: '#f44336',
        light: '#e57373',
        dark: '#d32f2f',
    },
    info: {
        main: '#2196f3',
        light: '#64b5f6',
        dark: '#1976d2',
    },
    background: {
        default: '#fafafa',
        paper: '#ffffff',
    },
    text: {
        primary: 'rgba(0, 0, 0, 0.87)',
        secondary: 'rgba(0, 0, 0, 0.6)',
    },
}

// Create Material-UI theme
export const theme = createTheme({
    palette,
    typography: {
        fontFamily: [
            'Roboto',
            'Noto Sans Devanagari', // For Hindi support
            'Noto Sans Tamil', // For Tamil support
            'Noto Sans Telugu', // For Telugu support
            'Noto Sans Kannada', // For Kannada support
            'Noto Sans Malayalam', // For Malayalam support
            'Noto Sans Gujarati', // For Gujarati support
            'Noto Sans Gurmukhi', // For Punjabi support
            'Noto Sans Bengali', // For Bengali support
            'Arial',
            'sans-serif',
        ].join(','),
        h1: {
            fontSize: '2.5rem',
            fontWeight: 600,
            lineHeight: 1.2,
        },
        h2: {
            fontSize: '2rem',
            fontWeight: 600,
            lineHeight: 1.3,
        },
        h3: {
            fontSize: '1.75rem',
            fontWeight: 600,
            lineHeight: 1.3,
        },
        h4: {
            fontSize: '1.5rem',
            fontWeight: 600,
            lineHeight: 1.4,
        },
        h5: {
            fontSize: '1.25rem',
            fontWeight: 600,
            lineHeight: 1.4,
        },
        h6: {
            fontSize: '1rem',
            fontWeight: 600,
            lineHeight: 1.5,
        },
        body1: {
            fontSize: '1rem',
            lineHeight: 1.5,
        },
        body2: {
            fontSize: '0.875rem',
            lineHeight: 1.43,
        },
        button: {
            textTransform: 'none',
            fontWeight: 500,
        },
    },
    shape: {
        borderRadius: 8,
    },
    spacing: 8,
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    padding: '8px 16px',
                    fontWeight: 500,
                    textTransform: 'none',
                },
                contained: {
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    '&:hover': {
                        boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                    },
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    '&:hover': {
                        boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                    },
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: 16,
                    fontWeight: 500,
                },
            },
        },
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 8,
                    },
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                },
            },
        },
        MuiDrawer: {
            styleOverrides: {
                paper: {
                    borderRadius: '0 12px 12px 0',
                },
            },
        },
        MuiDialog: {
            styleOverrides: {
                paper: {
                    borderRadius: 12,
                },
            },
        },
        MuiSnackbar: {
            styleOverrides: {
                root: {
                    '& .MuiSnackbarContent-root': {
                        borderRadius: 8,
                    },
                },
            },
        },
    },
    breakpoints: {
        values: {
            xs: 0,
            sm: 600,
            md: 900,
            lg: 1200,
            xl: 1536,
        },
    },
})

// Dark theme variant (for future use)
export const darkTheme = createTheme({
    ...theme,
    palette: {
        ...theme.palette,
        mode: 'dark',
        background: {
            default: '#121212',
            paper: '#1e1e1e',
        },
        text: {
            primary: '#ffffff',
            secondary: 'rgba(255, 255, 255, 0.7)',
        },
    },
})