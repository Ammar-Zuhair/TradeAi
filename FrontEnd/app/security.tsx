import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    Alert,
    Switch
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Lock, ArrowLeft, Save, Fingerprint } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
// import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/api';
import Layout from '@/constants/Layout';
import Button from '@/components/Button';

export default function SecurityScreen() {
    const { colors } = useTheme();
    const { user } = useAuth();

    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
    });

    const [isLoading, setIsLoading] = useState(false);
    const [biometricEnabled, setBiometricEnabled] = useState(false);
    const [isBiometricAvailable, setIsBiometricAvailable] = useState(false);

    useEffect(() => {
        checkBiometricAvailability();
        loadBiometricPreference();
    }, []);

    const checkBiometricAvailability = async () => {
        // Biometric disabled - uncomment after installing expo-local-authentication properly
        setIsBiometricAvailable(false);
        /*
        try {
            if (!LocalAuthentication) {
                setIsBiometricAvailable(false);
                return;
            }
            const compatible = await LocalAuthentication.hasHardwareAsync();
            const enrolled = await LocalAuthentication.isEnrolledAsync();
            setIsBiometricAvailable(compatible && enrolled);
        } catch (error) {
            console.log('Biometric not available:', error);
            setIsBiometricAvailable(false);
        }
        */
    };

    const loadBiometricPreference = async () => {
        try {
            const enabled = await AsyncStorage.getItem('biometricEnabled');
            setBiometricEnabled(enabled === 'true');
        } catch (error) {
            console.error('Error loading biometric preference:', error);
        }
    };

    const handlePasswordChange = async () => {
        // Validation
        if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
            Alert.alert('Error', 'Please fill in all password fields');
            return;
        }

        if (passwordData.newPassword.length < 8) {
            Alert.alert('Error', 'New password must be at least 8 characters');
            return;
        }

        if (passwordData.newPassword !== passwordData.confirmPassword) {
            Alert.alert('Error', 'New passwords do not match');
            return;
        }

        setIsLoading(true);
        try {
            if (!user?.token) {
                Alert.alert('Error', 'Not authenticated');
                return;
            }

            // Call API to change password
            await authService.changePassword(
                user.token,
                passwordData.currentPassword,
                passwordData.newPassword
            );

            Alert.alert(
                'Success',
                'Password changed successfully. Please log in again with your new password.',
                [
                    {
                        text: 'OK',
                        onPress: async () => {
                            // Sign out user
                            await AsyncStorage.removeItem('user');
                            router.replace('/login');
                        }
                    }
                ]
            );

            // Clear form
            setPasswordData({
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
            });
        } catch (error: any) {
            console.error('Error changing password:', error);
            const errorMessage = error.response?.data?.detail ||
                error.response?.data?.message ||
                'Failed to change password';
            Alert.alert('Error', errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleBiometric = async (value: boolean) => {
        // Biometric disabled - uncomment after installing expo-local-authentication properly
        Alert.alert('Info', 'Biometric authentication is temporarily disabled. It will be available in the next update.');
        /*
        try {
            if (value && isBiometricAvailable && LocalAuthentication) {
                // Test biometric authentication
                const result = await LocalAuthentication.authenticateAsync({
                    promptMessage: 'Authenticate to enable biometric login',
                    fallbackLabel: 'Use passcode',
                });

                if (result.success) {
                    setBiometricEnabled(true);
                    await AsyncStorage.setItem('biometricEnabled', 'true');
                    Alert.alert('Success', 'Biometric login enabled');
                } else {
                    Alert.alert('Error', 'Biometric authentication failed');
                }
            } else {
                setBiometricEnabled(false);
                await AsyncStorage.setItem('biometricEnabled', 'false');
                if (value) {
                    Alert.alert('Info', 'Biometric authentication is not available');
                } else {
                    Alert.alert('Success', 'Biometric login disabled');
                }
            }
        } catch (error) {
            console.log('Error toggling biometric:', error);
            Alert.alert('Error', 'Failed to toggle biometric authentication');
        }
        */
    };

    // Dynamic styles
    const themeStyles = {
        container: { backgroundColor: colors.surface },
        title: { color: colors.text },
        sectionTitle: { color: colors.text },
        sectionDescription: { color: colors.placeholder },
        inputContainer: {
            backgroundColor: colors.card,
            borderColor: colors.border,
        },
        input: { color: colors.text },
        placeholder: colors.placeholder,
        icon: colors.placeholder,
        label: { color: colors.text },
        biometricCard: { backgroundColor: colors.card, borderColor: colors.border },
        biometricText: { color: colors.text },
        biometricDescription: { color: colors.placeholder },
    };

    return (
        <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ArrowLeft size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={[styles.title, themeStyles.title]}>Security</Text>
                <View style={{ width: 24 }} />
            </View>

            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.keyboardView}
            >
                <ScrollView
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                >
                    {/* Change Password Section */}
                    <Animated.View entering={FadeInDown.delay(200).springify()} style={styles.section}>
                        <Text style={[styles.sectionTitle, themeStyles.sectionTitle]}>Change Password</Text>
                        <Text style={[styles.sectionDescription, themeStyles.sectionDescription]}>
                            Update your password to keep your account secure
                        </Text>

                        <View style={styles.form}>
                            {/* Current Password */}
                            <View style={styles.inputGroup}>
                                <Text style={[styles.label, themeStyles.label]}>Current Password</Text>
                                <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                    <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                    <TextInput
                                        style={[styles.input, themeStyles.input]}
                                        value={passwordData.currentPassword}
                                        onChangeText={(text) => setPasswordData({ ...passwordData, currentPassword: text })}
                                        placeholder="Enter current password"
                                        placeholderTextColor={themeStyles.placeholder}
                                        secureTextEntry
                                    />
                                </View>
                            </View>

                            {/* New Password */}
                            <View style={styles.inputGroup}>
                                <Text style={[styles.label, themeStyles.label]}>New Password</Text>
                                <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                    <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                    <TextInput
                                        style={[styles.input, themeStyles.input]}
                                        value={passwordData.newPassword}
                                        onChangeText={(text) => setPasswordData({ ...passwordData, newPassword: text })}
                                        placeholder="Enter new password (min 8 characters)"
                                        placeholderTextColor={themeStyles.placeholder}
                                        secureTextEntry
                                    />
                                </View>
                            </View>

                            {/* Confirm New Password */}
                            <View style={styles.inputGroup}>
                                <Text style={[styles.label, themeStyles.label]}>Confirm New Password</Text>
                                <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                    <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                    <TextInput
                                        style={[styles.input, themeStyles.input]}
                                        value={passwordData.confirmPassword}
                                        onChangeText={(text) => setPasswordData({ ...passwordData, confirmPassword: text })}
                                        placeholder="Re-enter new password"
                                        placeholderTextColor={themeStyles.placeholder}
                                        secureTextEntry
                                    />
                                </View>
                            </View>

                            <Button
                                title="Change Password"
                                onPress={handlePasswordChange}
                                isLoading={isLoading}
                                buttonStyle={styles.saveButton}
                                leftIcon={<Save size={20} color="#fff" />}
                            />
                        </View>
                    </Animated.View>

                    {/* Biometric Authentication Section */}
                    <Animated.View entering={FadeInDown.delay(400).springify()} style={styles.section}>
                        <Text style={[styles.sectionTitle, themeStyles.sectionTitle]}>Biometric Authentication</Text>
                        <Text style={[styles.sectionDescription, themeStyles.sectionDescription]}>
                            Use fingerprint or face recognition to log in quickly
                        </Text>

                        <View style={[styles.biometricCard, themeStyles.biometricCard]}>
                            <View style={styles.biometricLeft}>
                                <Fingerprint size={24} color={colors.primary} />
                                <View style={styles.biometricTextContainer}>
                                    <Text style={[styles.biometricText, themeStyles.biometricText]}>
                                        Enable Biometric Login
                                    </Text>
                                    <Text style={[styles.biometricDescription, themeStyles.biometricDescription]}>
                                        {isBiometricAvailable
                                            ? 'Log in with your fingerprint or face'
                                            : 'Biometric authentication not available on this device'}
                                    </Text>
                                </View>
                            </View>
                            <Switch
                                value={biometricEnabled}
                                onValueChange={toggleBiometric}
                                disabled={!isBiometricAvailable}
                                trackColor={{ false: '#767577', true: colors.primary }}
                                thumbColor="#f4f3f4"
                            />
                        </View>
                    </Animated.View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: Layout.spacing.md,
        paddingVertical: Layout.spacing.md,
    },
    backButton: {
        padding: Layout.spacing.xs,
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
        fontFamily: 'Inter-Bold',
    },
    keyboardView: {
        flex: 1,
    },
    scrollContent: {
        padding: Layout.spacing.lg,
    },
    section: {
        marginBottom: Layout.spacing.xxl,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        fontFamily: 'Inter-Bold',
        marginBottom: Layout.spacing.xs,
    },
    sectionDescription: {
        fontSize: 14,
        marginBottom: Layout.spacing.lg,
    },
    form: {
        gap: Layout.spacing.lg,
    },
    inputGroup: {
        gap: Layout.spacing.xs,
    },
    label: {
        fontSize: 14,
        fontWeight: '500',
        fontFamily: 'Inter-Medium',
        marginLeft: 4,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1,
        borderRadius: Layout.borderRadius.md,
        height: 50,
        paddingHorizontal: Layout.spacing.md,
    },
    inputIcon: {
        marginRight: Layout.spacing.sm,
    },
    input: {
        flex: 1,
        fontSize: 16,
        height: '100%',
    },
    saveButton: {
        marginTop: Layout.spacing.sm,
    },
    biometricCard: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: Layout.spacing.md,
        borderRadius: Layout.borderRadius.lg,
        borderWidth: 1,
    },
    biometricLeft: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
        gap: Layout.spacing.md,
    },
    biometricTextContainer: {
        flex: 1,
    },
    biometricText: {
        fontSize: 16,
        fontWeight: '500',
        fontFamily: 'Inter-Medium',
        marginBottom: 4,
    },
    biometricDescription: {
        fontSize: 12,
    },
});
