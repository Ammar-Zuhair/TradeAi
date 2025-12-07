import { useEffect } from 'react';
import { BackHandler, Alert, Platform } from 'react-native';
import { usePathname, useRouter } from 'expo-router';

/**
 * Custom hook to handle Android back button behavior
 * - Shows exit confirmation dialog on Home screen
 * - Navigates to Home screen from other tabs
 * - Allows normal back navigation on sub-screens
 */
export const useBackHandler = () => {
    const pathname = usePathname();
    const router = useRouter();

    useEffect(() => {
        // Only handle back button on Android
        if (Platform.OS !== 'android') {
            return;
        }

        const backAction = () => {
            console.log('🔙 Back Button Pressed');
            console.log('📍 Current Path:', pathname);
            console.log('❓ Can Go Back:', router.canGoBack());

            // 1. If we can go back in the stack, do it manually
            if (router.canGoBack()) {
                console.log('↩️ Navigating back');
                router.back();
                return true; // We handled it
            }

            // 2. If we are at the root of the navigation stack:
            const isHomeScreen = pathname === '/' || pathname === '/index' || pathname === '/(tabs)/index';

            if (isHomeScreen) {
                // Show exit confirmation dialog
                Alert.alert(
                    'مغادرة التطبيق',
                    'هل أنت متأكد أنك تريد المغادرة؟',
                    [
                        {
                            text: 'إلغاء',
                            onPress: () => null,
                            style: 'cancel',
                        },
                        {
                            text: 'مغادرة',
                            onPress: () => BackHandler.exitApp(),
                        },
                    ],
                    { cancelable: false }
                );
                return true; // We handled it
            } else {
                // If on any other root screen, go to Home
                console.log('🏠 Going Home');
                router.replace('/');
                return true; // We handled it
            }
        };

        const backHandler = BackHandler.addEventListener(
            'hardwareBackPress',
            backAction
        );

        return () => backHandler.remove();
    }, [pathname, router]);
};
