# Property-Based Tests for Multilingual Mandi

## Vernacular Typography Support Test

### Overview
This directory contains property-based tests for the Multilingual Mandi platform, specifically testing the vernacular typography support feature.

### Test File: `vernacularTypography.property.test.js`

**Purpose**: Tests Property 55 - Vernacular Typography Support  
**Validates**: Requirements 12.2 - Support vernacular typography for authentic regional language representation

### What is Tested

The property-based test validates that the `CulturalText` component correctly:

1. **Font Class Assignment**: Applies the correct font class for any supported Indian language
2. **Script-Font Mapping Consistency**: Uses consistent font classes for languages sharing the same script
3. **RTL Language Support**: Correctly identifies and handles RTL languages (Arabic-based scripts)
4. **Language Coverage**: Supports all major Indian languages implemented in the component
5. **Font Class Format**: Uses consistent naming convention for font classes
6. **Text Rendering Integrity**: Preserves text content regardless of language or variant
7. **Fallback Behavior**: Handles unsupported language codes gracefully

### Supported Languages

The test validates support for 13 major Indian languages:
- Hindi (Devanagari script)
- English (Latin script)
- Tamil (Tamil script)
- Telugu (Telugu script)
- Bengali (Bengali script)
- Marathi (Devanagari script)
- Gujarati (Gujarati script)
- Kannada (Kannada script)
- Malayalam (Malayalam script)
- Punjabi (Gurmukhi script)
- Odia (Oriya script)
- Assamese (Bengali script)
- Urdu (Arabic script, RTL)

### Property-Based Testing Approach

Uses `fast-check` library to generate random test cases and validate universal properties:
- **50 test runs** for font class assignment validation
- **100 test runs** for text content preservation
- **20 test runs** for RTL language support and fallback behavior
- **10 test runs** for script consistency validation

### Key Features Validated

1. **Typography Classes**: Ensures proper CSS font classes are applied
2. **Script Support**: Validates different writing systems (Devanagari, Tamil, Bengali, etc.)
3. **RTL Support**: Tests right-to-left language handling
4. **Fallback Mechanism**: Ensures graceful degradation for unsupported languages
5. **Text Variants**: Tests different typography variants (heading, subheading, body, caption)

### Running the Tests

```bash
npm test vernacularTypography.property.test.js
```

### Test Results

All 7 property tests pass, validating that the vernacular typography support meets the requirements for authentic regional language representation in the Multilingual Mandi platform.