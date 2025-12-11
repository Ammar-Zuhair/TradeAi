import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, TextInput, TouchableOpacity, ScrollView } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ArrowLeft, Mail } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { authService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import Colors from '@/constants/Colors';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Button from '@/components/Button';

export default function VerifyEmailScreen() {
    const params = useLocalSearchParams();
    const { setUser } = useAuth();
    const email = params.email as string;
    const name = params.name as string;
    const password = params.password as string;
    const idCardNumber = params.idCardNumber as string;
    const phoneNumber = params.phoneNumber as string;
    const address = params.address as string;
    const dateOfBirth = params.dateOfBirth as string;

    const [otp, setOtp] = useState(['', '', '', '', '', '']);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
    const [canResend, setCanResend] = useState(false);

    const inputRefs = useRef<(TextInput | null)[]>([]);

    // Countdown timer
    useEffect(() => {
        if (timeLeft > 0) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        } else {
            setCanResend(true);
        }
    }, [timeLeft]);

    const handleOtpChange = (value: string, index: number) => {
        if (!/^\d*$/.test(value)) return; // Only numbers

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);
        setError('');

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit when all 6 digits entered
        if (index === 5 && value && newOtp.every(digit => digit)) {
            handleVerify(newOtp.join(''));
        }
    };

    const handleKeyPress = (e: any, index: number) => {
        if (e.nativeEvent.key === 'Backspace' && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handleVerify = async (otpCode?: string) => {
        const code = otpCode || otp.join('');

        if (code.length !== 6) {
            setError('Please enter all 6 digits');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            // Register with OTP (backend verifies OTP during registration)
            const registerResponse = await authService.register(
                name,
                email,
                password,
                code,
                {
                    idCardNumber,
                    phoneNumber,
                    address,
                    dateOfBirth
                }
            );

            // Create user object
            const appUser = {
                id: registerResponse.user.UserID.toString(),
                name: registerResponse.user.UserName,
                email: registerResponse.user.UserEmail,
                token: registerResponse.access_token,
                phoneNumber: registerResponse.user.PhoneNumber,
                address: registerResponse.user.Address,
                idCardNumber: registerResponse.user.UserIDCardrNumber ? registerResponse.user.UserIDCardrNumber.toString() : undefined,
                dateOfBirth: registerResponse.user.DateOfBirth
            };

            // Save user to storage
            await AsyncStorage.setItem('user', JSON.stringify(appUser));

            // Sync with AuthContext - THIS WAS MISSING
            setUser(appUser);

            router.replace('/(tabs)');
        } catch (err: any) {
            setError(err.response?.data?.message || 'Verification failed. Please try again.');
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } finally {
            setIsLoading(false);
        }
    };

    const handleResend = async () => {
        if (!canResend) return;

        setIsLoading(true);
        setError('');

        try {
            await authService.sendOTP(email, name);
            setTimeLeft(300);
            setCanResend(false);
            setOtp(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to resend OTP');
        } finally {
            setIsLoading(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
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
                <Mail size={60} color={Colors.trading.primary} />
                <HeadingText style={styles.title}>Verify Your Email</HeadingText>
                <BodyText style={styles.subtitle}>
                    We've sent a 6-digit code to{'\n'}
                    <BodyText style={styles.email}>{email}</BodyText>
                </BodyText>
            </View>

            <View style={styles.formContainer}>
                {error && (
                    <View style={styles.errorContainer}>
                        <BodyText style={styles.errorText}>{error}</BodyText>
                    </View>
                )}

                <View style={styles.otpContainer}>
                    {otp.map((digit, index) => (
                        <TextInput
                            key={index}
                            ref={ref => { inputRefs.current[index] = ref; }}
                            style={[
                                styles.otpInput,
                                digit && styles.otpInputFilled,
                                error && styles.otpInputError
                            ]}
                            value={digit}
                            onChangeText={(value) => handleOtpChange(value, index)}
                            onKeyPress={(e) => handleKeyPress(e, index)}
                            keyboardType="number-pad"
                            maxLength={1}
                            selectTextOnFocus
                            // Force LTR for OTP input even in RTL mode
                            textAlign='center'
                        />
                    ))}
                </View>

                <View style={styles.timerContainer}>
                    <BodyText style={styles.timerText}>
                        {canResend ? 'Code expired' : `Code expires in ${formatTime(timeLeft)}`}
                    </BodyText>
                </View>

                <Button
                    title="Verify Email"
                    isLoading={isLoading}
                    onPress={() => handleVerify()}
                    buttonStyle={styles.verifyButton}
                />

                <TouchableOpacity
                    style={styles.resendButton}
                    onPress={handleResend}
                    disabled={!canResend || isLoading}
                >
                    <BodyText style={[
                        styles.resendText,
                        (!canResend || isLoading) && styles.resendTextDisabled
                    ]}>
                        {canResend ? 'Resend Code' : 'Resend available after expiry'}
                    </BodyText>
                </TouchableOpacity>
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
        marginTop: 20,
        marginBottom: 16,
    },
    subtitle: {
        fontSize: 16,
        color: Colors.trading.placeholder,
        textAlign: 'center',
        lineHeight: 24,
    },
    email: {
        color: Colors.trading.primary,
        fontWeight: '600',
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
        textAlign: 'center',
    },
    otpContainer: {
        flexDirection: 'row',
        direction: 'ltr', // Force Left-to-Right layout
        justifyContent: 'space-between',
        marginBottom: Layout.spacing.lg,
    },
    otpInput: {
        width: 50,
        height: 60,
        borderRadius: Layout.borderRadius.md,
        backgroundColor: Colors.trading.card,
        borderWidth: 2,
        borderColor: Colors.trading.border,
        color: '#fff',
        fontSize: 24,
        fontWeight: '700',
        textAlign: 'center',
    },
    otpInputFilled: {
        borderColor: Colors.trading.primary,
    },
    otpInputError: {
        borderColor: Colors.trading.negative,
    },
    timerContainer: {
        alignItems: 'center',
        marginBottom: Layout.spacing.xl,
    },
    timerText: {
        color: Colors.trading.placeholder,
        fontSize: 14,
    },
    verifyButton: {
        marginBottom: Layout.spacing.md,
    },
    resendButton: {
        alignItems: 'center',
        padding: Layout.spacing.md,
    },
    resendText: {
        color: Colors.trading.primary,
        fontSize: 16,
    },
    resendTextDisabled: {
        color: Colors.trading.placeholder,
    },
});
