/**
 * Property-Based Test for Local Vendor Promotion
 * 
 * Tests Property 56: Local Vendor Promotion
 * Validates Requirements 12.3: Promote the 'Vocal for Local' initiative by highlighting local vendors and products
 */

import fc from 'fast-check';
import { LocalVendorService, mockVendors, mockProducts } from '../services/localVendorService.js';
import { afterEach, beforeEach, describe, test, expect } from 'vitest';

describe('Property 56: Local Vendor Promotion', () => {
  let localVendorService;

  beforeEach(() => {
    localVendorService = new LocalVendorService();
    // Clear localStorage to ensure clean state
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  // Arbitraries for property-based testing
  const locationArbitrary = fc.record({
    coordinates: fc.record({
      lat: fc.float({ min: 8.0, max: 37.0 }), // India's latitude range
      lng: fc.float({ min: 68.0, max: 97.0 }) // India's longitude range
    }),
    state: fc.constantFrom('Uttar Pradesh', 'Punjab', 'Tamil Nadu', 'Maharashtra', 'Gujarat'),
    district: fc.string({ minLength: 3, maxLength: 20 })
  });

  const preferencesArbitrary = fc.record({
    preferLocal: fc.boolean(),
    maxDistance: fc.integer({ min: 10, max: 100 }),
    preferredLanguages: fc.array(fc.constantFrom('hi', 'en', 'ta', 'te', 'pa'), { minLength: 1, maxLength: 3 }),
    preferOrganic: fc.boolean(),
    supportSmallFarmers: fc.boolean()
  });

  const filtersArbitrary = fc.record({
    localOnly: fc.boolean(),
    maxDistance: fc.option(fc.integer({ min: 5, max: 200 })),
    language: fc.option(fc.constantFrom('hi', 'en', 'ta', 'te', 'pa')),
    category: fc.option(fc.constantFrom('grains', 'dairy', 'spices', 'vegetables', 'oils'))
  });

  test('local vendors should always be prioritized in search results when preferLocal is true', () => {
    fc.assert(fc.property(
      preferencesArbitrary.filter(prefs => prefs.preferLocal === true),
      filtersArbitrary,
      async (preferences, filters) => {
        localVendorService.savePreferences(preferences);
        
        const result = await localVendorService.getLocalVendors(filters);
        
        expect(result.success).toBe(true);
        expect(result.vendors).toBeDefined();
        
        // Property: Local vendors should appear before non-local vendors
        let foundNonLocal = false;
        for (const vendor of result.vendors) {
          if (!vendor.isLocal) {
            foundNonLocal = true;
          } else if (foundNonLocal) {
            // If we found a local vendor after a non-local one, the ordering is wrong
            expect(false).toBe(true); // This should not happen
          }
        }
        
        return true;
      }
    ), { numRuns: 30 });
  });

  test('distance-based vendor sorting should work correctly for local vendors', () => {
    fc.assert(fc.property(
      locationArbitrary,
      filtersArbitrary,
      async (userLocation, filters) => {
        localVendorService.setUserLocation(userLocation);
        
        const result = await localVendorService.getLocalVendors({ ...filters, localOnly: true });
        
        expect(result.success).toBe(true);
        
        // Property: Local vendors should be sorted by distance (ascending)
        const localVendors = result.vendors.filter(v => v.isLocal);
        for (let i = 1; i < localVendors.length; i++) {
          expect(localVendors[i].distance).toBeGreaterThanOrEqual(localVendors[i - 1].distance);
        }
        
        return true;
      }
    ), { numRuns: 25 });
  });

  test('regional specialty products should be properly promoted', () => {
    fc.assert(fc.property(
      fc.record({
        regionalSpecialty: fc.boolean(),
        category: fc.option(fc.constantFrom('grains', 'dairy', 'spices', 'vegetables', 'oils'))
      }),
      async (filters) => {
        const result = await localVendorService.getLocalProducts(filters);
        
        expect(result.success).toBe(true);
        expect(result.products).toBeDefined();
        
        // Property: When regionalSpecialty filter is true, all returned products should be regional specialties
        if (filters.regionalSpecialty) {
          result.products.forEach(product => {
            expect(product.regionalSpecialty).toBe(true);
          });
        }
        
        // Property: All returned products should be local products by default
        result.products.forEach(product => {
          expect(product.isLocalProduct).toBe(true);
        });
        
        return true;
      }
    ), { numRuns: 20 });
  });

  test('local market statistics should be accurate and consistent', () => {
    fc.assert(fc.property(
      fc.constant(true),
      async () => {
        const result = await localVendorService.getLocalMarketStats();
        
        expect(result.success).toBe(true);
        expect(result.stats).toBeDefined();
        
        const stats = result.stats;
        
        // Property: Percentages should be mathematically correct
        const expectedLocalVendorPercentage = Math.round((stats.localVendors / stats.totalVendors) * 100);
        expect(stats.localVendorPercentage).toBe(expectedLocalVendorPercentage);
        
        const expectedLocalProductPercentage = Math.round((stats.localProducts / stats.totalProducts) * 100);
        expect(stats.localProductPercentage).toBe(expectedLocalProductPercentage);
        
        const expectedOrganicPercentage = Math.round((stats.organicProducts / stats.totalProducts) * 100);
        expect(stats.organicPercentage).toBe(expectedOrganicPercentage);
        
        // Property: Counts should be non-negative and logical
        expect(stats.totalVendors).toBeGreaterThanOrEqual(0);
        expect(stats.localVendors).toBeGreaterThanOrEqual(0);
        expect(stats.localVendors).toBeLessThanOrEqual(stats.totalVendors);
        expect(stats.totalProducts).toBeGreaterThanOrEqual(0);
        expect(stats.localProducts).toBeLessThanOrEqual(stats.totalProducts);
        expect(stats.organicProducts).toBeLessThanOrEqual(stats.totalProducts);
        
        // Property: Average rating should be within valid range
        expect(stats.averageRating).toBeGreaterThanOrEqual(0);
        expect(stats.averageRating).toBeLessThanOrEqual(5);
        
        return true;
      }
    ), { numRuns: 10 });
  });

  test('preference settings should affect vendor promotion correctly', () => {
    fc.assert(fc.property(
      preferencesArbitrary,
      async (preferences) => {
        localVendorService.savePreferences(preferences);
        
        const result = await localVendorService.getVendorRecommendations();
        
        expect(result.success).toBe(true);
        expect(result.recommendations).toBeDefined();
        
        // Property: When preferLocal is true, only local vendors should be recommended
        if (preferences.preferLocal) {
          result.recommendations.forEach(vendor => {
            expect(vendor.isLocal).toBe(true);
          });
        }
        
        // Property: When preferOrganic is true, recommended vendors should have organic products
        if (preferences.preferOrganic) {
          result.recommendations.forEach(vendor => {
            const hasOrganicProducts = vendor.products.some(product => product.organic);
            expect(hasOrganicProducts).toBe(true);
          });
        }
        
        // Property: Recommended vendors should support at least one preferred language
        if (preferences.preferredLanguages.length > 0) {
          result.recommendations.forEach(vendor => {
            const hasCommonLanguage = vendor.languages.some(lang => 
              preferences.preferredLanguages.includes(lang)
            );
            expect(hasCommonLanguage).toBe(true);
          });
        }
        
        return true;
      }
    ), { numRuns: 40 });
  });

  test('search functionality should prioritize local vendors in results', () => {
    fc.assert(fc.property(
      fc.string({ minLength: 1, maxLength: 10 }),
      fc.record({
        localOnly: fc.boolean(),
        maxDistance: fc.option(fc.integer({ min: 10, max: 100 }))
      }),
      async (searchQuery, filters) => {
        const result = await localVendorService.searchLocalVendors(searchQuery, filters);
        
        expect(result.success).toBe(true);
        expect(result.results).toBeDefined();
        expect(result.query).toBe(searchQuery.toLowerCase());
        
        // Property: When localOnly is true, all results should be local vendors
        if (filters.localOnly) {
          result.results.forEach(vendor => {
            expect(vendor.isLocal).toBe(true);
          });
        }
        
        // Property: Local vendors should appear before non-local vendors in search results
        let foundNonLocal = false;
        for (const vendor of result.results) {
          if (!vendor.isLocal) {
            foundNonLocal = true;
          } else if (foundNonLocal) {
            // Local vendor found after non-local vendor indicates wrong ordering
            expect(false).toBe(true);
          }
        }
        
        return true;
      }
    ), { numRuns: 25 });
  });

  test('urban-rural connection should facilitate proper vendor matching', () => {
    fc.assert(fc.property(
      fc.record({
        location: locationArbitrary,
        languages: fc.array(fc.constantFrom('hi', 'en', 'ta', 'te', 'pa'), { minLength: 1, maxLength: 3 })
      }),
      fc.record({
        categories: fc.array(fc.constantFrom('grains', 'dairy', 'spices', 'vegetables', 'oils'), { minLength: 1, maxLength: 3 }),
        qualityPreference: fc.constantFrom('premium', 'standard', 'basic'),
        preferOrganic: fc.boolean()
      }),
      async (buyerProfile, requirements) => {
        const result = await localVendorService.facilitateUrbanRuralConnection(buyerProfile, requirements);
        
        expect(result.success).toBe(true);
        expect(result.connections).toBeDefined();
        
        // Property: All connected vendors should have matching products
        result.connections.forEach(connection => {
          const hasMatchingProducts = connection.vendor.products.some(product =>
            requirements.categories.includes(product.category)
          );
          expect(hasMatchingProducts).toBe(true);
        });
        
        // Property: Connections should be sorted by compatibility score (descending)
        for (let i = 1; i < result.connections.length; i++) {
          expect(result.connections[i].compatibilityScore)
            .toBeLessThanOrEqual(result.connections[i - 1].compatibilityScore);
        }
        
        // Property: When preferOrganic is true, connected vendors should have organic products
        if (requirements.preferOrganic) {
          result.connections.forEach(connection => {
            const hasOrganicProducts = connection.vendor.products.some(product => product.organic);
            expect(hasOrganicProducts).toBe(true);
          });
        }
        
        return true;
      }
    ), { numRuns: 20 });
  });

  test('local vendor promotion should maintain data consistency across operations', () => {
    fc.assert(fc.property(
      preferencesArbitrary,
      filtersArbitrary,
      async (preferences, filters) => {
        localVendorService.savePreferences(preferences);
        
        // Get vendors and products simultaneously
        const [vendorResult, productResult, statsResult] = await Promise.all([
          localVendorService.getLocalVendors(filters),
          localVendorService.getLocalProducts(filters),
          localVendorService.getLocalMarketStats()
        ]);
        
        expect(vendorResult.success).toBe(true);
        expect(productResult.success).toBe(true);
        expect(statsResult.success).toBe(true);
        
        // Property: Local vendor count should be consistent across operations
        const localVendorsFromSearch = vendorResult.vendors.filter(v => v.isLocal).length;
        const localVendorsFromStats = statsResult.stats.localVendors;
        
        // The search might filter vendors, so local count should be <= stats count
        expect(localVendorsFromSearch).toBeLessThanOrEqual(localVendorsFromStats);
        
        // Property: Product-vendor relationships should be maintained
        productResult.products.forEach(product => {
          if (product.vendor) {
            expect(product.vendorId).toBe(product.vendor.id);
          }
        });
        
        return true;
      }
    ), { numRuns: 15 });
  });
});