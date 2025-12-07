import React, { createContext, useContext, useState, useEffect } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Colors from '@/constants/Colors';

type Theme = 'light' | 'dark';

interface ThemeContextType {
    theme: Theme;
    isDarkMode: boolean;
    colors: typeof Colors.dark & typeof Colors.trading;
    toggleTheme: () => void;
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const systemColorScheme = useColorScheme();
    const [theme, setThemeState] = useState<Theme>('dark'); // Default to dark
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        loadTheme();
    }, []);

    const loadTheme = async () => {
        try {
            const savedTheme = await AsyncStorage.getItem('user-theme');
            if (savedTheme) {
                setThemeState(savedTheme as Theme);
            } else {
                // If no saved theme, default to dark as requested
                setThemeState('dark');
            }
        } catch (error) {
            console.error('Failed to load theme:', error);
        } finally {
            setIsLoaded(true);
        }
    };

    const setTheme = async (newTheme: Theme) => {
        try {
            setThemeState(newTheme);
            await AsyncStorage.setItem('user-theme', newTheme);
        } catch (error) {
            console.error('Failed to save theme:', error);
        }
    };

    const toggleTheme = () => {
        setTheme(theme === 'dark' ? 'light' : 'dark');
    };

    const isDarkMode = theme === 'dark';

    // Merge specific theme colors with common trading colors
    const activeColors = {
        ...Colors[theme],
        ...Colors.trading, // Base trading colors
        // Override specific trading colors based on theme if needed
        background: Colors[theme].background,
        text: Colors[theme].text,
        tint: Colors[theme].tint,
        // Add more dynamic overrides here if Colors.trading has static values that need to change
        card: isDarkMode ? Colors.trading.card : '#f5f5f5', // Example override for light mode card
        border: isDarkMode ? Colors.trading.border : '#e0e0e0',
        surface: isDarkMode ? Colors.trading.surface : '#ffffff',
        // Ensure these exist as they are used in settings
        placeholder: Colors.trading.placeholder,
        primary: Colors.trading.primary,
        accent: Colors.trading.accent,
        negative: Colors.trading.negative,
    };

    if (!isLoaded) {
        return null; // Or a loading spinner
    }

    return (
        <ThemeContext.Provider value={{ theme, isDarkMode, colors: activeColors, toggleTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
