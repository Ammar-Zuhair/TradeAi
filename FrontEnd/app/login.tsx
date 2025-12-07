import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Image, TouchableOpacity, ScrollView } from 'react-native';
import { router } from 'expo-router';
import { Lock, Mail, ArrowRight, Fingerprint } from 'lucide-react-native';
import Animated, { useSharedValue, useAnimatedStyle, withTiming, Easing } from 'react-native-reanimated';
// import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Input from '@/components/Input';
import Button from '@/components/Button';
import TextButton from '@/components/TextButton';

export default function LoginScreen() {
  const { signIn, googleSignIn, facebookSignIn, isLoading, error, clearError } = useAuth();
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const formOpacity = useSharedValue(0);
  const formTranslateY = useSharedValue(50);

  useEffect(() => {
    // Animation for form entrance
    formOpacity.value = withTiming(1, { duration: 600, easing: Easing.out(Easing.ease) });
    formTranslateY.value = withTiming(0, { duration: 600, easing: Easing.out(Easing.ease) });

    // Clear errors on component mount
    clearError();

    // Biometric authentication disabled - uncomment after installing expo-local-authentication
    // checkBiometric();
  }, []);

  const checkBiometric = async () => {
    // Biometric disabled for now
    return;
    /*
    try {
      const biometricEnabled = await AsyncStorage.getItem('biometricEnabled');
      const savedUser = await AsyncStorage.getItem('user');
      
      if (biometricEnabled === 'true' && savedUser) {
        const user = JSON.parse(savedUser);
        
        // Check if LocalAuthentication is available
        if (!LocalAuthentication) {
          console.log('LocalAuthentication not available');
          return;
        }
        
        const compatible = await LocalAuthentication.hasHardwareAsync();
        const enrolled = await LocalAuthentication.isEnrolledAsync();
        
        if (compatible && enrolled && user.email) {
          // Auto-prompt biometric
          setTimeout(() => handleBiometricLogin(), 500);
        }
      }
    } catch (error) {
      console.log('Biometric not available:', error);
    }
    */
  };

  const handleBiometricLogin = async () => {
    // Biometric disabled for now
    return;
    /*
    try {
      const savedUser = await AsyncStorage.getItem('user');
      if (!savedUser || !LocalAuthentication) {
        return;
      }

      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate to log in',
        fallbackLabel: 'Use password',
      });

      if (result.success) {
        const user = JSON.parse(savedUser);
        // User is already authenticated via biometric, navigate to app
        router.replace('/(tabs)');
      }
    } catch (error) {
      console.log('Biometric authentication error:', error);
    }
    */
  };

  const formAnimatedStyle = useAnimatedStyle(() => {
    return {
      opacity: formOpacity.value,
      transform: [{ translateY: formTranslateY.value }],
    };
  });

  const validateForm = () => {
    let isValid = true;
    setEmailError('');
    setPasswordError('');

    if (!email.trim()) {
      setEmailError('Email is required');
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setEmailError('Please enter a valid email');
      isValid = false;
    }

    if (!password) {
      setPasswordError('Password is required');
      isValid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      isValid = false;
    }

    return isValid;
  };

  const handleLogin = async () => {
    if (validateForm()) {
      await signIn(email, password);
    }
  };

  const handleGoogleSignIn = async () => {
    await googleSignIn();
  };

  const handleFacebookSignIn = async () => {
    await facebookSignIn();
  };

  const handleForgotPassword = () => {
    router.push('/forgot-password');
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    subtitle: { color: colors.placeholder },
    errorText: { color: colors.negative },
    signupText: { color: colors.placeholder },
    signupLink: { color: colors.primary },
    dividerLine: { backgroundColor: colors.border },
    dividerText: { color: colors.placeholder },
  };

  return (
    <ScrollView
      style={[styles.container, themeStyles.container]}
      contentContainerStyle={styles.contentContainer}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Image
          source={{ uri: 'https://images.pexels.com/photos/7567445/pexels-photo-7567445.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2' }}
          style={styles.logo}
        />
        <HeadingText style={[styles.title, themeStyles.title]}>TradeAI</HeadingText>
        <BodyText style={[styles.subtitle, themeStyles.subtitle]}>Sign in to your account</BodyText>
      </View>

      <Animated.View style={[styles.formContainer, formAnimatedStyle]}>
        {error && (
          <View style={styles.errorContainer}>
            <BodyText style={[styles.errorText, themeStyles.errorText]}>{error}</BodyText>
          </View>
        )}

        <Input
          label="Email"
          placeholder="Enter your email"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
          error={emailError}
          leftIcon={<Mail size={20} color={colors.placeholder} />}
        />

        <Input
          label="Password"
          placeholder="Enter your password"
          isPassword
          value={password}
          onChangeText={setPassword}
          error={passwordError}
          leftIcon={<Lock size={20} color={colors.placeholder} />}
        />

        <TextButton
          title="Forgot Password?"
          style={styles.forgotPassword}
          onPress={handleForgotPassword}
        />

        <Button
          title="Sign In"
          isLoading={isLoading}
          onPress={handleLogin}
          rightIcon={<ArrowRight size={20} color="#fff" />}
        />

        <View style={styles.signupContainer}>
          <BodyText style={[styles.signupText, themeStyles.signupText]}>Don't have an account?</BodyText>
          <TouchableOpacity onPress={() => router.push('/signup')}>
            <BodyText style={[styles.signupLink, themeStyles.signupLink]}>Sign Up</BodyText>
          </TouchableOpacity>
        </View>

        <View style={styles.divider}>
          <View style={[styles.dividerLine, themeStyles.dividerLine]} />
          <BodyText style={[styles.dividerText, themeStyles.dividerText]}>OR</BodyText>
          <View style={[styles.dividerLine, themeStyles.dividerLine]} />
        </View>

        <Button
          title="Sign in with Google"
          variant="secondary"
          onPress={handleGoogleSignIn}
          buttonStyle={styles.socialButton}
        />

        <Button
          title="Sign in with Facebook"
          variant="secondary"
          onPress={handleFacebookSignIn}
          buttonStyle={styles.socialButton}
        />
      </Animated.View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: Layout.spacing.lg,
    paddingBottom: Layout.spacing.xxl,
  },
  header: {
    alignItems: 'center',
    marginTop: 80,
    marginBottom: 40,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
  },
  formContainer: {
    width: '100%',
  },
  errorContainer: {
    backgroundColor: 'rgba(255, 71, 87, 0.2)',
    borderRadius: Layout.borderRadius.md,
    padding: Layout.spacing.md,
    marginBottom: Layout.spacing.md,
  },
  errorText: {
    fontSize: 14,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: Layout.spacing.md,
  },
  signupContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: Layout.spacing.lg,
    marginBottom: Layout.spacing.lg,
  },
  signupText: {
  },
  signupLink: {
    fontWeight: '600',
    marginLeft: Layout.spacing.xs,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: Layout.spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
  },
  dividerText: {
    paddingHorizontal: Layout.spacing.md,
    fontSize: 14,
  },
  socialButton: {
    marginBottom: Layout.spacing.md,
  },
});