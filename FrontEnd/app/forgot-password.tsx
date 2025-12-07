import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { Mail, ArrowLeft, ArrowRight } from 'lucide-react-native';

import { authService } from '@/services/api';
import Colors from '@/constants/Colors';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Input from '@/components/Input';
import Button from '@/components/Button';

export default function ForgotPasswordScreen() {
    const [email, setEmail] = useState('');
    const [emailError, setEmailError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [errorMessage, setErrorMessage] = useState('');

    const validateEmail = () => {
        setEmailError('');

        if (!email.trim()) {
            setEmailError('Email is required');
            return false;
        } else if (!/\S+@\S+\.\S+/.test(email)) {
            setEmailError('Please enter a valid email');
            return false;
        }

        return true;
    };

    const handleSubmit = async () => {
        if (!validateEmail()) return;

        setIsLoading(true);
        setErrorMessage('');
        setSuccessMessage('');

        try {
            const response = await authService.requestPasswordReset(email);
            setSuccessMessage(response.message || 'If an account exists with this email, you will receive password reset instructions.');
            setEmail('');
        } catch (error: any) {
            setErrorMessage(error.response?.data?.message || 'Failed to send reset email. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ScrollView
            style={styles.container}
            contentContainerStyle={styles.contentContainer}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
        >
            <View style={styles.header}>
                <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => router.back()}
                >
                    <ArrowLeft size={24} color="#fff" />
                </TouchableOpacity>
                <HeadingText style={styles.title}>Forgot Password?</HeadingText>
                <BodyText style={styles.subtitle}>
                    Enter your email address and we'll send you instructions to reset your password.
                </BodyText>
            </View>

            <View style={styles.formContainer}>
                {successMessage ? (
                    <View style={styles.successContainer}>
                        <BodyText style={styles.successText}>{successMessage}</BodyText>
                        <Button
                            title="Back to Login"
                            onPress={() => router.push('/login')}
                            buttonStyle={styles.backToLoginButton}
                        />
                    </View>
                ) : (
                    <>
                        {errorMessage && (
                            <View style={styles.errorContainer}>
                                <BodyText style={styles.errorText}>{errorMessage}</BodyText>
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
                            leftIcon={<Mail size={20} color={Colors.trading.placeholder} />}
                        />

                        <Button
                            title="Send Reset Link"
                            isLoading={isLoading}
                            onPress={handleSubmit}
                            rightIcon={<ArrowRight size={20} color="#fff" />}
                            buttonStyle={styles.submitButton}
                        />

                        <TouchableOpacity
                            style={styles.backToLoginLink}
                            onPress={() => router.push('/login')}
                        >
                            <BodyText style={styles.backToLoginText}>Back to Login</BodyText>
                        </TouchableOpacity>
                    </>
                )}
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: Colors.trading.surface,
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
    backButton: {
        position: 'absolute',
        left: 0,
        top: -10,
        padding: Layout.spacing.sm,
    },
    title: {
        fontSize: 28,
        color: '#fff',
        marginBottom: 16,
    },
    subtitle: {
        fontSize: 16,
        color: Colors.trading.placeholder,
        textAlign: 'center',
        paddingHorizontal: Layout.spacing.md,
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
        color: Colors.trading.negative,
        fontSize: 14,
    },
    successContainer: {
        backgroundColor: 'rgba(39, 174, 96, 0.2)',
        borderRadius: Layout.borderRadius.md,
        padding: Layout.spacing.lg,
        marginBottom: Layout.spacing.xl,
    },
    successText: {
        color: Colors.trading.positive,
        fontSize: 14,
        textAlign: 'center',
        marginBottom: Layout.spacing.lg,
    },
    submitButton: {
        marginTop: Layout.spacing.md,
    },
    backToLoginButton: {
        marginTop: Layout.spacing.md,
    },
    backToLoginLink: {
        alignItems: 'center',
        marginTop: Layout.spacing.xl,
    },
    backToLoginText: {
        color: Colors.trading.primary,
        fontSize: 16,
    },
});
