// Test file for Cultural Elements Components
// Tests Requirements 12.1, 12.2, and 9.6

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
    CulturalText,
    CulturalCard,
    CulturalButton,
    LanguageSelector,
    CulturalInput,
    CulturalStatusIndicator,
    CulturalHeader,
    CulturalLoader,
    CulturalAlert
} from '../components/CulturalElements';

describe('Cultural Elements Components', () => {

    describe('CulturalText', () => {
        test('renders text with correct language font class', () => {
            render(
                <CulturalText language="hi" variant="heading">
                    स्वागत है
                </CulturalText>
            );

            const textElement = screen.getByText('स्वागत है');
            expect(textElement).toHaveClass('font-devanagari');
            expect(textElement).toHaveClass('text-2xl');
            expect(textElement).toHaveClass('font-bold');
        });

        test('applies correct font for Tamil language', () => {
            render(
                <CulturalText language="ta" variant="body">
                    தமிழ்
                </CulturalText>
            );

            const textElement = screen.getByText('தமிழ்');
            expect(textElement).toHaveClass('font-tamil');
        });

        test('defaults to English font for unsupported language', () => {
            render(
                <CulturalText language="xyz" variant="body">
                    Test Text
                </CulturalText>
            );

            const textElement = screen.getByText('Test Text');
            expect(textElement).not.toHaveClass('font-devanagari');
        });
    });

    describe('CulturalCard', () => {
        test('renders with default cultural styling', () => {
            render(
                <CulturalCard>
                    <p>Card Content</p>
                </CulturalCard>
            );

            const cardElement = screen.getByText('Card Content').parentElement;
            expect(cardElement).toHaveClass('cultural-card');
        });

        test('applies tricolor border when specified', () => {
            render(
                <CulturalCard showTricolorBorder={true}>
                    <p>Card with Border</p>
                </CulturalCard>
            );

            const cardElement = screen.getByText('Card with Border').parentElement;
            expect(cardElement).toHaveClass('cultural-pattern-border');
        });
    });

    describe('CulturalButton', () => {
        test('renders with primary variant styling', () => {
            const handleClick = jest.fn();
            render(
                <CulturalButton onClick={handleClick} variant="primary">
                    Click Me
                </CulturalButton>
            );

            const buttonElement = screen.getByRole('button', { name: 'Click Me' });
            expect(buttonElement).toHaveClass('cultural-button');
        });

        test('handles click events correctly', () => {
            const handleClick = jest.fn();
            render(
                <CulturalButton onClick={handleClick}>
                    Click Me
                </CulturalButton>
            );

            const buttonElement = screen.getByRole('button', { name: 'Click Me' });
            fireEvent.click(buttonElement);
            expect(handleClick).toHaveBeenCalledTimes(1);
        });

        test('is disabled when disabled prop is true', () => {
            render(
                <CulturalButton disabled={true}>
                    Disabled Button
                </CulturalButton>
            );

            const buttonElement = screen.getByRole('button', { name: 'Disabled Button' });
            expect(buttonElement).toBeDisabled();
            expect(buttonElement).toHaveClass('opacity-50');
        });

        test('applies pulse animation when showPulse is true', () => {
            render(
                <CulturalButton showPulse={true}>
                    Pulsing Button
                </CulturalButton>
            );

            const buttonElement = screen.getByRole('button', { name: 'Pulsing Button' });
            expect(buttonElement).toHaveClass('cultural-pulse');
        });
    });

    describe('LanguageSelector', () => {
        test('renders with default languages', () => {
            const handleLanguageChange = jest.fn();
            render(
                <LanguageSelector
                    selectedLanguage="hi"
                    onLanguageChange={handleLanguageChange}
                />
            );

            const selectElement = screen.getByRole('combobox');
            expect(selectElement).toHaveValue('hi');
            expect(selectElement).toHaveClass('language-selector');
        });

        test('calls onLanguageChange when selection changes', () => {
            const handleLanguageChange = jest.fn();
            render(
                <LanguageSelector
                    selectedLanguage="hi"
                    onLanguageChange={handleLanguageChange}
                />
            );

            const selectElement = screen.getByRole('combobox');
            fireEvent.change(selectElement, { target: { value: 'ta' } });
            expect(handleLanguageChange).toHaveBeenCalledWith('ta');
        });

        test('displays custom languages when provided', () => {
            const customLanguages = [
                { code: 'hi', name: 'हिंदी', flag: '🇮🇳' },
                { code: 'en', name: 'English', flag: '🇬🇧' }
            ];

            render(
                <LanguageSelector
                    selectedLanguage="hi"
                    onLanguageChange={() => { }}
                    languages={customLanguages}
                />
            );

            const options = screen.getAllByRole('option');
            expect(options).toHaveLength(2);
        });
    });

    describe('CulturalInput', () => {
        test('renders with cultural styling', () => {
            render(
                <CulturalInput
                    placeholder="Enter text"
                    value=""
                    onChange={() => { }}
                />
            );

            const inputElement = screen.getByPlaceholderText('Enter text');
            expect(inputElement).toHaveClass('cultural-input');
        });

        test('applies correct font for specified language', () => {
            render(
                <CulturalInput
                    language="hi"
                    placeholder="अपना नाम दर्ज करें"
                    value=""
                    onChange={() => { }}
                />
            );

            const inputElement = screen.getByPlaceholderText('अपना नाम दर्ज करें');
            expect(inputElement).toHaveClass('font-devanagari');
        });

        test('handles value changes correctly', () => {
            const handleChange = jest.fn();
            render(
                <CulturalInput
                    value=""
                    onChange={handleChange}
                    placeholder="Test input"
                />
            );

            const inputElement = screen.getByPlaceholderText('Test input');
            fireEvent.change(inputElement, { target: { value: 'test value' } });
            expect(handleChange).toHaveBeenCalled();
        });
    });

    describe('CulturalStatusIndicator', () => {
        test('renders online status correctly', () => {
            render(<CulturalStatusIndicator status="online" />);

            const statusElement = screen.getByText(/Online/);
            expect(statusElement).toHaveClass('status-online');
            expect(screen.getByText('🟢')).toBeInTheDocument();
        });

        test('renders offline status correctly', () => {
            render(<CulturalStatusIndicator status="offline" />);

            const statusElement = screen.getByText(/Offline/);
            expect(statusElement).toHaveClass('status-offline');
            expect(screen.getByText('🔴')).toBeInTheDocument();
        });

        test('renders connecting status correctly', () => {
            render(<CulturalStatusIndicator status="connecting" />);

            const statusElement = screen.getByText(/Connecting/);
            expect(statusElement).toHaveClass('status-connecting');
            expect(screen.getByText('🟡')).toBeInTheDocument();
        });

        test('hides icon when showIcon is false', () => {
            render(<CulturalStatusIndicator status="online" showIcon={false} />);

            expect(screen.queryByText('🟢')).not.toBeInTheDocument();
            expect(screen.getByText(/Online/)).toBeInTheDocument();
        });
    });

    describe('CulturalHeader', () => {
        test('renders title and subtitle correctly', () => {
            render(
                <CulturalHeader
                    title="Test Title"
                    subtitle="Test Subtitle"
                    showFlag={true}
                />
            );

            expect(screen.getByText('Test Title')).toBeInTheDocument();
            expect(screen.getByText('Test Subtitle')).toBeInTheDocument();
            expect(screen.getByText('🇮🇳')).toBeInTheDocument();
        });

        test('hides flag when showFlag is false', () => {
            render(
                <CulturalHeader
                    title="Test Title"
                    showFlag={false}
                />
            );

            expect(screen.getByText('Test Title')).toBeInTheDocument();
            expect(screen.queryByText('🇮🇳')).not.toBeInTheDocument();
        });
    });

    describe('CulturalLoader', () => {
        test('renders with default message', () => {
            render(<CulturalLoader />);

            expect(screen.getByText(/Loading/)).toBeInTheDocument();
            expect(screen.getByText(/लोड हो रहा है/)).toBeInTheDocument();
        });

        test('renders with custom message', () => {
            render(<CulturalLoader message="Custom loading message" />);

            expect(screen.getByText('Custom loading message')).toBeInTheDocument();
        });

        test('applies correct size classes', () => {
            const { container } = render(<CulturalLoader size="large" />);

            const spinner = container.querySelector('.w-16');
            expect(spinner).toBeInTheDocument();
        });
    });

    describe('CulturalAlert', () => {
        test('renders success alert correctly', () => {
            render(
                <CulturalAlert
                    type="success"
                    title="Success"
                    message="Operation completed successfully"
                />
            );

            expect(screen.getByText('Success')).toBeInTheDocument();
            expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
            expect(screen.getByText('✅')).toBeInTheDocument();
        });

        test('renders error alert correctly', () => {
            render(
                <CulturalAlert
                    type="error"
                    title="Error"
                    message="Something went wrong"
                />
            );

            expect(screen.getByText('Error')).toBeInTheDocument();
            expect(screen.getByText('Something went wrong')).toBeInTheDocument();
            expect(screen.getByText('❌')).toBeInTheDocument();
        });

        test('calls onClose when close button is clicked', () => {
            const handleClose = jest.fn();
            render(
                <CulturalAlert
                    type="info"
                    message="Info message"
                    onClose={handleClose}
                />
            );

            const closeButton = screen.getByText('×');
            fireEvent.click(closeButton);
            expect(handleClose).toHaveBeenCalledTimes(1);
        });
    });
});

// Integration tests for cultural theme functionality
describe('Cultural Theme Integration', () => {
    test('components work together in a complete interface', () => {
        const TestInterface = () => {
            const [language, setLanguage] = React.useState('hi');
            const [inputValue, setInputValue] = React.useState('');

            return (
                <div>
                    <CulturalHeader
                        title="Test Interface"
                        subtitle="Testing cultural components"
                    />

                    <CulturalCard>
                        <LanguageSelector
                            selectedLanguage={language}
                            onLanguageChange={setLanguage}
                        />

                        <CulturalInput
                            language={language}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Enter text"
                        />

                        <CulturalButton variant="primary">
                            Submit
                        </CulturalButton>
                    </CulturalCard>

                    <CulturalStatusIndicator status="online" />
                </div>
            );
        };

        render(<TestInterface />);

        // Verify all components render
        expect(screen.getByText('Test Interface')).toBeInTheDocument();
        expect(screen.getByRole('combobox')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
        expect(screen.getByText(/Online/)).toBeInTheDocument();
    });
});