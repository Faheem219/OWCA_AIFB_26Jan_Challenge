import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import VocalForLocal from '../components/VocalForLocal';
import localVendorService from '../services/localVendorService';

// Mock the localVendorService
vi.mock('../services/localVendorService', () => ({
    default: {
        getLocalVendors: vi.fn(),
        getLocalProducts: vi.fn(),
        getLocalMarketStats: vi.fn(),
        loadPreferences: vi.fn(),
        savePreferences: vi.fn(),
        searchLocalVendors: vi.fn(),
        facilitateUrbanRuralConnection: vi.fn()
    }
}));

describe('VocalForLocal Component', () => {
    const mockVendors = [
        {
            id: 'vendor_001',
            name: 'राम किसान',
            englishName: 'Ram Kisan',
            location: {
                state: 'Uttar Pradesh',
                district: 'Meerut',
                village: 'Sardhana'
            },
            isLocal: true,
            distance: 5.2,
            rating: 4.7,
            specialties: ['wheat', 'rice'],
            products: []
        }
    ];

    const mockProducts = [
        {
            id: 'prod_001',
            name: 'गेहूं',
            englishName: 'Wheat',
            category: 'grains',
            price: 2200,
            unit: 'quintal',
            organic: true,
            isLocalProduct: true,
            vendor: mockVendors[0]
        }
    ];

    const mockStats = {
        totalVendors: 10,
        localVendors: 8,
        localVendorPercentage: 80,
        averageRating: 4.5,
        organicPercentage: 60
    };

    beforeEach(() => {
        // Reset all mocks
        vi.clearAllMocks();

        // Setup default mock responses
        localVendorService.getLocalVendors.mockResolvedValue({
            success: true,
            vendors: mockVendors,
            totalCount: mockVendors.length,
            localCount: mockVendors.length
        });

        localVendorService.getLocalProducts.mockResolvedValue({
            success: true,
            products: mockProducts,
            totalCount: mockProducts.length
        });

        localVendorService.getLocalMarketStats.mockResolvedValue({
            success: true,
            stats: mockStats
        });

        localVendorService.loadPreferences.mockReturnValue({
            preferLocal: true,
            maxDistance: 50,
            preferOrganic: true,
            supportSmallFarmers: true
        });
    });

    it('renders VocalForLocal component with title', async () => {
        render(<VocalForLocal language="hi" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText(/वोकल फॉर लोकल/)).toBeInTheDocument();
        });
    });

    it('displays market statistics', async () => {
        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('Statistics')).toBeInTheDocument();
            expect(screen.getByText('10')).toBeInTheDocument(); // Total vendors
            expect(screen.getByText('80%')).toBeInTheDocument(); // Local percentage
        });
    });

    it('renders local vendors', async () => {
        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('Ram Kisan')).toBeInTheDocument();
            expect(screen.getByText('Meerut, Uttar Pradesh')).toBeInTheDocument();
            expect(screen.getByText('5.2km')).toBeInTheDocument();
        });
    });

    it('renders local products', async () => {
        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('Wheat')).toBeInTheDocument();
            expect(screen.getByText('₹2200/quintal')).toBeInTheDocument();
        });
    });

    it('handles search functionality', async () => {
        const mockSearchResults = [mockVendors[0]];
        localVendorService.searchLocalVendors.mockResolvedValue({
            success: true,
            results: mockSearchResults,
            totalCount: 1
        });

        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        const searchInput = screen.getByPlaceholderText(/Search vendors or products/);
        const searchButton = screen.getByText('Discover');

        fireEvent.change(searchInput, { target: { value: 'wheat' } });
        fireEvent.click(searchButton);

        await waitFor(() => {
            expect(localVendorService.searchLocalVendors).toHaveBeenCalledWith('wheat', {
                localOnly: true
            });
        });
    });

    it('switches between tabs', async () => {
        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('Local Vendors')).toBeInTheDocument();
        });

        const connectTab = screen.getByText('Connect');
        fireEvent.click(connectTab);

        expect(screen.getByText('Rural Connection')).toBeInTheDocument();
    });

    it('handles urban-rural connection', async () => {
        const mockConnections = [
            {
                vendor: mockVendors[0],
                compatibilityScore: 85,
                commonLanguages: ['hi', 'en'],
                matchingProducts: mockProducts,
                estimatedDeliveryTime: '1-2 days'
            }
        ];

        localVendorService.facilitateUrbanRuralConnection.mockResolvedValue({
            success: true,
            connections: mockConnections,
            totalMatches: 1
        });

        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        const connectTab = screen.getByText('Connect');
        fireEvent.click(connectTab);

        await waitFor(() => {
            const connectButton = screen.getByText('Connect');
            fireEvent.click(connectButton);
        });

        await waitFor(() => {
            expect(localVendorService.facilitateUrbanRuralConnection).toHaveBeenCalled();
        });
    });

    it('saves preferences', async () => {
        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        const settingsTab = screen.getByText('Settings');
        fireEvent.click(settingsTab);

        await waitFor(() => {
            const saveButton = screen.getByText('Save');
            fireEvent.click(saveButton);

            expect(localVendorService.savePreferences).toHaveBeenCalled();
        });
    });

    it('displays content in Hindi when language is set to Hindi', async () => {
        render(<VocalForLocal language="hi" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('वोकल फॉर लोकल')).toBeInTheDocument();
            expect(screen.getByText('स्थानीय विक्रेताओं को बढ़ावा दें')).toBeInTheDocument();
            expect(screen.getByText('स्थानीय विक्रेता')).toBeInTheDocument();
        });
    });

    it('displays content in Tamil when language is set to Tamil', async () => {
        render(<VocalForLocal language="ta" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText('வோக்கல் ஃபார் லோக்கல்')).toBeInTheDocument();
            expect(screen.getByText('உள்ளூர் விற்பனையாளர்களை ஊக்குவிக்கவும்')).toBeInTheDocument();
        });
    });

    it('handles loading states', async () => {
        // Mock delayed response
        localVendorService.getLocalVendors.mockImplementation(() =>
            new Promise(resolve => setTimeout(() => resolve({
                success: true,
                vendors: mockVendors,
                totalCount: mockVendors.length,
                localCount: mockVendors.length
            }), 100))
        );

        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        // Should show loading initially
        expect(screen.getByText(/Loading/)).toBeInTheDocument();

        // Wait for loading to complete
        await waitFor(() => {
            expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
        }, { timeout: 2000 });
    });

    it('handles error states', async () => {
        localVendorService.getLocalVendors.mockResolvedValue({
            success: false,
            error: 'Network error',
            vendors: [],
            totalCount: 0,
            localCount: 0
        });

        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
        });
    });
});

// Property-based test for vendor data validation
describe('VocalForLocal Property Tests', () => {
    it('should handle various vendor data structures', async () => {
        const testVendors = [
            {
                id: 'test_1',
                name: 'Test Vendor',
                englishName: 'Test Vendor',
                location: { state: 'Test State', district: 'Test District' },
                isLocal: true,
                distance: 10,
                rating: 4.5,
                specialties: ['test'],
                products: []
            },
            {
                id: 'test_2',
                name: 'टेस्ट विक्रेता',
                englishName: 'Test Vendor 2',
                location: { state: 'Test State 2', district: 'Test District 2' },
                isLocal: false,
                distance: 25,
                rating: 3.8,
                specialties: ['test1', 'test2'],
                products: []
            }
        ];

        localVendorService.getLocalVendors.mockResolvedValue({
            success: true,
            vendors: testVendors,
            totalCount: testVendors.length,
            localCount: 1
        });

        render(<VocalForLocal language="en" onLanguageChange={() => { }} />);

        await waitFor(() => {
            testVendors.forEach(vendor => {
                expect(screen.getByText(vendor.englishName)).toBeInTheDocument();
                expect(screen.getByText(`${vendor.location.district}, ${vendor.location.state}`)).toBeInTheDocument();
            });
        });
    });
});