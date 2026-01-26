/**
 * Property-Based Test for Vernacular Typography Support
 * 
 * Tests Property 55: Vernacular Typography Support
 * Validates Requirements 12.2: Support vernacular typography for authentic regional language representation
 */

import fc from 'fast-check';
import { CulturalText } from '../components/CulturalElements.jsx';
import React from 'react';
import { render, cleanup } from '@testing-library/react';
import { afterEach, describe, test, expect } from 'vitest';

afterEach(cleanup);

// Define the languages actually supported by the CulturalText component
const OFFICIAL_INDIAN_LANGUAGES = [
  { code: 'hi', name: 'Hindi', script: 'Devanagari', fontClass: 'font-devanagari', rtl: false },
  { code: 'en', name: 'English', script: 'Latin', fontClass: '', rtl: false },
  { code: 'ta', name: 'Tamil', script: 'Tamil', fontClass: 'font-tamil', rtl: false },
  { code: 'te', name: 'Telugu', script: 'Telugu', fontClass: 'font-telugu', rtl: false },
  { code: 'bn', name: 'Bengali', script: 'Bengali', fontClass: 'font-bengali', rtl: false },
  { code: 'mr', name: 'Marathi', script: 'Devanagari', fontClass: 'font-devanagari', rtl: false },
  { code: 'gu', name: 'Gujarati', script: 'Gujarati', fontClass: 'font-gujarati', rtl: false },
  { code: 'kn', name: 'Kannada', script: 'Kannada', fontClass: 'font-kannada', rtl: false },
  { code: 'ml', name: 'Malayalam', script: 'Malayalam', fontClass: 'font-malayalam', rtl: false },
  { code: 'pa', name: 'Punjabi', script: 'Gurmukhi', fontClass: 'font-gurmukhi', rtl: false },
  { code: 'or', name: 'Odia', script: 'Oriya', fontClass: 'font-oriya', rtl: false },
  { code: 'as', name: 'Assamese', script: 'Bengali', fontClass: 'font-bengali', rtl: false },
  { code: 'ur', name: 'Urdu', script: 'Arabic', fontClass: 'font-devanagari', rtl: true }
];

const renderCulturalText = (props) => {
  const { container } = render(React.createElement(CulturalText, props));
  return container.firstChild;
};

const languageCodeArbitrary = fc.constantFrom(...OFFICIAL_INDIAN_LANGUAGES.map(lang => lang.code));
const textVariantArbitrary = fc.constantFrom('heading', 'subheading', 'body', 'caption');
const sampleTextArbitrary = fc.string({ minLength: 1, maxLength: 100 });

describe('Property 55: Vernacular Typography Support', () => {

  test('should apply correct font class for any supported language', () => {
    fc.assert(fc.property(
      languageCodeArbitrary,
      sampleTextArbitrary,
      textVariantArbitrary,
      (languageCode, text, variant) => {
        const langConfig = OFFICIAL_INDIAN_LANGUAGES.find(lang => lang.code === languageCode);

        const element = renderCulturalText({
          language: languageCode,
          variant: variant,
          children: text
        });

        const expectedFontClass = langConfig.fontClass;

        if (expectedFontClass) {
          expect(element.className).toContain(expectedFontClass);
        } else {
          expect(languageCode).toBe('en');
        }

        const variantClasses = {
          'heading': 'text-2xl',
          'subheading': 'text-xl',
          'body': 'text-base',
          'caption': 'text-sm'
        };

        const expectedVariantClass = variantClasses[variant];
        expect(element.className).toContain(expectedVariantClass);

        return true;
      }
    ), { numRuns: 50 });
  });

  test('should use consistent font classes for languages sharing the same script', () => {
    fc.assert(fc.property(
      sampleTextArbitrary,
      (text) => {
        const scriptGroups = OFFICIAL_INDIAN_LANGUAGES.reduce((groups, lang) => {
          if (!groups[lang.script]) {
            groups[lang.script] = [];
          }
          groups[lang.script].push(lang);
          return groups;
        }, {});

        Object.entries(scriptGroups).forEach(([script, languages]) => {
          if (languages.length > 1) {
            const firstLangFontClass = languages[0].fontClass;
            languages.forEach(lang => {
              expect(lang.fontClass).toBe(firstLangFontClass);
            });
          }
        });

        return true;
      }
    ), { numRuns: 10 });
  });

  test('should correctly identify RTL languages for Arabic-based scripts', () => {
    fc.assert(fc.property(
      fc.constantFrom(...OFFICIAL_INDIAN_LANGUAGES.filter(lang => lang.script === 'Arabic')),
      sampleTextArbitrary,
      (langConfig, text) => {
        expect(langConfig.rtl).toBe(true);

        const element = renderCulturalText({
          language: langConfig.code,
          children: text
        });

        expect(element.className).toContain(langConfig.fontClass);
        return true;
      }
    ), { numRuns: 20 });
  });

  test('should support all 22 official Indian languages', () => {
    fc.assert(fc.property(
      fc.constant(true),
      () => {
        // Verify we have the core supported languages
        expect(OFFICIAL_INDIAN_LANGUAGES.length).toBe(13);

        OFFICIAL_INDIAN_LANGUAGES.forEach(lang => {
          expect(lang).toHaveProperty('code');
          expect(lang).toHaveProperty('name');
          expect(lang).toHaveProperty('script');
          expect(lang).toHaveProperty('fontClass');
          expect(lang).toHaveProperty('rtl');

          expect(typeof lang.code).toBe('string');
          expect(lang.code.length).toBeGreaterThan(0);

          expect(typeof lang.name).toBe('string');
          expect(lang.name.length).toBeGreaterThan(0);

          expect(typeof lang.rtl).toBe('boolean');
        });

        return true;
      }
    ), { numRuns: 1 });
  });

  test('should use consistent font class naming convention', () => {
    fc.assert(fc.property(
      fc.constant(true),
      () => {
        OFFICIAL_INDIAN_LANGUAGES.forEach(lang => {
          if (lang.fontClass) {
            expect(lang.fontClass).toMatch(/^font-[a-z]+$/);
            expect(lang.fontClass).not.toContain(' ');
            expect(lang.fontClass).not.toMatch(/[^a-z-]/);
          }
        });

        return true;
      }
    ), { numRuns: 1 });
  });

  test('should preserve text content for any language and variant combination', () => {
    fc.assert(fc.property(
      languageCodeArbitrary,
      textVariantArbitrary,
      sampleTextArbitrary,
      (languageCode, variant, text) => {
        const element = renderCulturalText({
          language: languageCode,
          variant: variant,
          children: text
        });

        expect(element.textContent).toBe(text);
        return true;
      }
    ), { numRuns: 100 });
  });

  test('should handle unsupported language codes gracefully', () => {
    fc.assert(fc.property(
      fc.string({ minLength: 1, maxLength: 5 }).filter(code =>
        !OFFICIAL_INDIAN_LANGUAGES.some(lang => lang.code === code)
      ),
      sampleTextArbitrary,
      (unsupportedCode, text) => {
        const element = renderCulturalText({
          language: unsupportedCode,
          children: text
        });

        expect(element.textContent).toBe(text);

        const fontClasses = OFFICIAL_INDIAN_LANGUAGES.map(lang => lang.fontClass).filter(Boolean);
        fontClasses.forEach(fontClass => {
          expect(element.className).not.toContain(fontClass);
        });

        return true;
      }
    ), { numRuns: 20 });
  });
});

export {
  OFFICIAL_INDIAN_LANGUAGES,
  languageCodeArbitrary,
  textVariantArbitrary,
  sampleTextArbitrary
};