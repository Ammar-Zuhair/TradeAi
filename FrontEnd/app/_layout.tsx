import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFrameworkReady } from '@/hooks/useFrameworkReady';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_700Bold } from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import * as NavigationBar from 'expo-navigation-bar';
import { Platform } from 'react-native';
import { AuthProvider } from '@/contexts/AuthContext';
import { AccountsProvider } from '@/contexts/AccountsContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

// Prevent the splash screen from auto-hiding
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  useFrameworkReady();

  const [fontsLoaded, fontError] = useFonts({
    'Inter-Regular': Inter_400Regular,
    'Inter-Medium': Inter_500Medium,
    'Inter-Bold': Inter_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      // Hide the splash screen after fonts have loaded (or failed to load)
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  useEffect(() => {
    async function configureImmersiveMode() {
      if (Platform.OS === 'android') {
        // Hide the navigation bar (bottom buttons) and status bar
        await NavigationBar.setVisibilityAsync('hidden');
        await NavigationBar.setBehaviorAsync('overlay-swipe'); // Show on swipe up

        // Optional: Make it translucent if visible
        // await NavigationBar.setBackgroundColorAsync('#00000000');
      }
    }
    configureImmersiveMode();
  }, []);

  // If fonts aren't loaded and there's no error, return null to keep splash screen
  if (!fontsLoaded && !fontError) {
    return null;
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <ThemeProvider>
          <AuthProvider>
            <AccountsProvider>
              <Stack screenOptions={{ headerShown: false }}>
                <Stack.Screen name="index" />
                <Stack.Screen name="login" options={{ animation: 'slide_from_right' }} />
                <Stack.Screen name="signup" options={{ animation: 'slide_from_right' }} />
                <Stack.Screen name="(tabs)" options={{ animation: 'fade' }} />
                <Stack.Screen name="complete-profile" options={{ animation: 'slide_from_bottom', gestureEnabled: false }} />
                <Stack.Screen name="+not-found" />
              </Stack>
              <StatusBar style="light" hidden={true} />
            </AccountsProvider>
          </AuthProvider>
        </ThemeProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}