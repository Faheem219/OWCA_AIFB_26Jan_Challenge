import React, { useState, useEffect } from 'react'
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    Grid,
    Chip,
    Button,
    Alert,
    Divider,
    Avatar,
} from '@mui/material'
import { Edit, Warning, CheckCircle } from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { ProfileForm } from '../../components/profile/ProfileForm'
import { User, VendorProfile, BuyerProfile } from '../../types'

export const ProfilePage: React.FC = () => {
    const { t } = useTranslation()
    const { user, updateUser } = useAuth()
    const [isEditing, setIsEditing] = useState(false)
    const [profileData, setProfileData] = useState<User | VendorProfile | BuyerProfile | null>(null)

    useEffect(() => {
        if (user) {
            setProfileData(user)
        }
    }, [user])

    const handleProfileUpdate = (updatedUser: User | VendorProfile | BuyerProfile) => {
        setProfileData(updatedUser)
        updateUser(updatedUser)
        setIsEditing(false)
    }

    const getVerificationStatus = () => {
        if (!user) return null

        const { verificationStatus } = user
        const verifications = [
            { key: 'email', label: 'Email', verified: verificationStatus.isEmailVerified },
            { key: 'phone', label: 'Phone', verified: verificationStatus.isPhoneVerified },
            { key: 'identity', label: 'Identity', verified: verificationStatus.isIdentityVerified },
        ]

        if (user.role === 'VENDOR') {
            verifications.push({
                key: 'business',
                label: 'Business',
                verified: verificationStatus.isBusinessVerified,
            })
        }

        return verifications
    }

    const renderVerificationBadges = () => {
        const verifications = getVerificationStatus()
        if (!verifications) return null

        return (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
                {verifications.map((verification) => (
                    <Chip
                        key={verification.key}
                        icon={verification.verified ? <CheckCircle /> : <Warning />}
                        label={`${verification.label} ${verification.verified ? 'Verified' : 'Pending'}`}
                        color={verification.verified ? 'success' : 'warning'}
                        variant={verification.verified ? 'filled' : 'outlined'}
                        size="small"
                    />
                ))}
            </Box>
        )
    }

    const renderProfileInfo = () => {
        if (!profileData) return null

        return (
            <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Avatar
                                    sx={{ width: 60, height: 60, mr: 2 }}
                                    src="" // Profile image would go here
                                >
                                    {profileData.email.charAt(0).toUpperCase()}
                                </Avatar>
                                <Box>
                                    <Typography variant="h6">
                                        {profileData.role === 'VENDOR'
                                            ? (profileData as VendorProfile).businessName || 'Business Name'
                                            : profileData.email
                                        }
                                    </Typography>
                                    <Chip
                                        label={profileData.role}
                                        color="primary"
                                        size="small"
                                        sx={{ mt: 1 }}
                                    />
                                </Box>
                            </Box>

                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                <strong>Email:</strong> {profileData.email}
                            </Typography>

                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                <strong>Languages:</strong> {profileData.preferredLanguages.join(', ')}
                            </Typography>

                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                <strong>Location:</strong> {profileData.location.address || 'Not specified'}
                            </Typography>

                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                <strong>Member since:</strong> {new Date(profileData.createdAt).toLocaleDateString()}
                            </Typography>

                            {renderVerificationBadges()}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Role-specific Information */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                {profileData.role === 'VENDOR' ? 'Business Information' : 'Buyer Preferences'}
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            {profileData.role === 'VENDOR' ? (
                                <Box>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Business Type:</strong> {(profileData as VendorProfile).businessType || 'Not specified'}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Product Categories:</strong>
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                                        {(profileData as VendorProfile).productCategories?.map((category) => (
                                            <Chip key={category} label={category} size="small" variant="outlined" />
                                        )) || <Typography variant="body2" color="text.secondary">None specified</Typography>}
                                    </Box>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Market Location:</strong> {(profileData as VendorProfile).marketLocation || 'Not specified'}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Rating:</strong> {(profileData as VendorProfile).rating || 0}/5
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        <strong>Total Transactions:</strong> {(profileData as VendorProfile).totalTransactions || 0}
                                    </Typography>
                                </Box>
                            ) : (
                                <Box>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        <strong>Preferred Categories:</strong>
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                                        {(profileData as BuyerProfile).preferredCategories?.map((category) => (
                                            <Chip key={category} label={category} size="small" variant="outlined" />
                                        )) || <Typography variant="body2" color="text.secondary">None specified</Typography>}
                                    </Box>
                                    {(profileData as BuyerProfile).budgetRange && (
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            <strong>Budget Range:</strong> {(profileData as BuyerProfile).budgetRange!.currency} {(profileData as BuyerProfile).budgetRange!.min} - {(profileData as BuyerProfile).budgetRange!.max}
                                        </Typography>
                                    )}
                                    <Typography variant="body2" color="text.secondary">
                                        <strong>Purchase History:</strong> {(profileData as BuyerProfile).purchaseHistory?.length || 0} orders
                                    </Typography>
                                </Box>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Verification Status */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Account Verification
                            </Typography>
                            <Divider sx={{ mb: 2 }} />

                            {!profileData.verificationStatus.isEmailVerified && (
                                <Alert severity="warning" sx={{ mb: 2 }}>
                                    Please verify your email address to access all features.
                                </Alert>
                            )}

                            {profileData.role === 'VENDOR' && !profileData.verificationStatus.isBusinessVerified && (
                                <Alert severity="info" sx={{ mb: 2 }}>
                                    Complete business verification to build trust with buyers and access premium features.
                                </Alert>
                            )}

                            <Typography variant="body2" color="text.secondary">
                                Verification helps build trust in the marketplace and unlocks additional features.
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        )
    }

    if (!user) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ py: 4, textAlign: 'center' }}>
                    <Typography variant="h5" color="error">
                        Please log in to view your profile
                    </Typography>
                </Box>
            </Container>
        )
    }

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        {t('profile.title')}
                    </Typography>
                    {!isEditing && (
                        <Button
                            variant="contained"
                            startIcon={<Edit />}
                            onClick={() => setIsEditing(true)}
                        >
                            Edit Profile
                        </Button>
                    )}
                </Box>

                {isEditing ? (
                    <ProfileForm
                        user={profileData || user}
                        onUpdate={handleProfileUpdate}
                        onCancel={() => setIsEditing(false)}
                    />
                ) : (
                    renderProfileInfo()
                )}
            </Box>
        </Container>
    )
}