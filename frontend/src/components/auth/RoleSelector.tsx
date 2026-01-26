import React from 'react'
import {
    FormControl,
    FormLabel,
    RadioGroup,
    FormControlLabel,
    Radio,
    Card,
    CardContent,
    Typography,
    Box,
    useTheme,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { UserRole } from '../../types'
import { Store, ShoppingCart } from '@mui/icons-material'

interface RoleSelectorProps {
    selectedRole: UserRole | ''
    onChange: (role: UserRole) => void
    required?: boolean
    error?: boolean
    helperText?: string
}

export const RoleSelector: React.FC<RoleSelectorProps> = ({
    selectedRole,
    onChange,
    required = false,
    error = false,
    helperText,
}) => {
    const { t } = useTranslation()
    const theme = useTheme()

    const roles = [
        {
            value: 'VENDOR' as UserRole,
            label: t('auth.vendor'),
            description: t('auth.vendorDescription'),
            icon: <Store />,
        },
        {
            value: 'BUYER' as UserRole,
            label: t('auth.buyer'),
            description: t('auth.buyerDescription'),
            icon: <ShoppingCart />,
        },
    ]

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        onChange(event.target.value as UserRole)
    }

    return (
        <FormControl component="fieldset" fullWidth required={required} error={error}>
            <FormLabel component="legend" sx={{ mb: 2 }}>
                {t('auth.selectRole')}
            </FormLabel>
            <RadioGroup value={selectedRole} onChange={handleChange}>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
                    {roles.map((role) => (
                        <Card
                            key={role.value}
                            sx={{
                                flex: 1,
                                cursor: 'pointer',
                                border: selectedRole === role.value
                                    ? `2px solid ${theme.palette.primary.main}`
                                    : `1px solid ${theme.palette.divider}`,
                                '&:hover': {
                                    borderColor: theme.palette.primary.main,
                                    boxShadow: theme.shadows[2],
                                },
                                transition: 'all 0.2s ease-in-out',
                            }}
                            onClick={() => onChange(role.value)}
                        >
                            <CardContent sx={{ textAlign: 'center', py: 3 }}>
                                <FormControlLabel
                                    value={role.value}
                                    control={<Radio sx={{ display: 'none' }} />}
                                    label=""
                                    sx={{ m: 0 }}
                                />
                                <Box
                                    sx={{
                                        color: selectedRole === role.value
                                            ? theme.palette.primary.main
                                            : theme.palette.text.secondary,
                                        mb: 2,
                                    }}
                                >
                                    {React.cloneElement(role.icon, { fontSize: 'large' })}
                                </Box>
                                <Typography
                                    variant="h6"
                                    gutterBottom
                                    sx={{
                                        color: selectedRole === role.value
                                            ? theme.palette.primary.main
                                            : theme.palette.text.primary,
                                        fontWeight: 600,
                                    }}
                                >
                                    {role.label}
                                </Typography>
                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ fontSize: '0.875rem' }}
                                >
                                    {role.description}
                                </Typography>
                            </CardContent>
                        </Card>
                    ))}
                </Box>
            </RadioGroup>
            {helperText && (
                <Box sx={{ mt: 1, fontSize: '0.75rem', color: error ? 'error.main' : 'text.secondary' }}>
                    {helperText}
                </Box>
            )}
        </FormControl>
    )
}