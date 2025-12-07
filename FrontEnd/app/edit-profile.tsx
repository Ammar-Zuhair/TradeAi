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
    Alert
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { User, Phone, MapPin, Calendar, CreditCard, ArrowLeft, Save } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Layout from '@/constants/Layout';
import Button from '@/components/Button';

export default function EditProfileScreen() {
    const { colors } = useTheme();
    const { user, setUser } = useAuth();

    // Load user data from AuthContext
    const [formData, setFormData] = useState({
        name: user?.name || '',
        idCardNumber: user?.idCardNumber || '',
        phoneNumber: user?.phoneNumber || '',
        address: user?.address || '',
        dateOfBirth: user?.dateOfBirth || '',
    });

    const [isLoading, setIsLoading] = useState(false);

    // Update form data when user data changes
    useEffect(() => {
        console.log('👤 User data in edit-profile:', user);
        if (user) {
            setFormData({
                name: user.name || '',
                idCardNumber: user.idCardNumber || '',
                phoneNumber: user.phoneNumber || '',
                address: user.address || '',
                dateOfBirth: user.dateOfBirth || '',
            });
        }
    }, [user]);

    const handleSave = async () => {
        setIsLoading(true);
        try {
            if (!user?.token) {
                Alert.alert('Error', 'Not authenticated');
                return;
            }

            // Prepare update data - only send fields that have values
            const updateData: any = {};

            if (formData.name) {
                updateData.UserIDcardrName = formData.name;
            }

            if (formData.idCardNumber) {
                const idNumber = parseInt(formData.idCardNumber);
                if (!isNaN(idNumber)) {
                    updateData.UserIDCardrNumber = idNumber;
                }
            }

            if (formData.phoneNumber) {
                updateData.PhoneNumber = formData.phoneNumber;
            }

            if (formData.address) {
                updateData.Address = formData.address;
            }

            if (formData.dateOfBirth) {
                updateData.DateOfBirth = formData.dateOfBirth;
            }

            console.log('📤 Sending update data:', updateData);

            // Call API to update profile
            const updatedUser = await authService.updateProfile(user.token, updateData);

            console.log('✅ Profile updated:', updatedUser);

            // Update user in AuthContext and AsyncStorage
            const newUserData = {
                ...user,
                name: updatedUser.UserIDcardrName,
                idCardNumber: updatedUser.UserIDCardrNumber?.toString(),
                phoneNumber: updatedUser.PhoneNumber,
                address: updatedUser.Address,
                dateOfBirth: updatedUser.DateOfBirth,
            };

            await AsyncStorage.setItem('user', JSON.stringify(newUserData));
            setUser(newUserData);

            Alert.alert('Success', 'Profile updated successfully');
            router.back();
        } catch (error: any) {
            console.error('❌ Error updating profile:', error);
            console.error('Error response:', error.response?.data);
            const errorMessage = error.response?.data?.detail ||
                error.response?.data?.message ||
                'Failed to update profile';
            Alert.alert('Error', errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // Dynamic styles
    const themeStyles = {
        container: { backgroundColor: colors.surface },
        title: { color: colors.text },
        inputContainer: {
            backgroundColor: colors.card,
            borderColor: colors.border,
        },
        input: { color: colors.text },
        placeholder: colors.placeholder,
        icon: colors.placeholder,
        label: { color: colors.text },
    };

    return (
        <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
                    <ArrowLeft size={24} color={colors.text} />
                </TouchableOpacity>
                <Text style={[styles.title, themeStyles.title]}>Edit Profile</Text>
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
                    <Animated.View entering={FadeInDown.delay(200).springify()} style={styles.form}>

                        {/* Full Name */}
                        <View style={styles.inputGroup}>
                            <Text style={[styles.label, themeStyles.label]}>Full Name</Text>
                            <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                <User size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                <TextInput
                                    style={[styles.input, themeStyles.input]}
                                    value={formData.name}
                                    onChangeText={(text) => setFormData({ ...formData, name: text })}
                                    placeholder="Full Name"
                                    placeholderTextColor={themeStyles.placeholder}
                                />
                            </View>
                        </View>

                        {/* ID Card Number */}
                        <View style={styles.inputGroup}>
                            <Text style={[styles.label, themeStyles.label]}>ID Card Number</Text>
                            <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                <CreditCard size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                <TextInput
                                    style={[styles.input, themeStyles.input]}
                                    value={formData.idCardNumber}
                                    onChangeText={(text) => setFormData({ ...formData, idCardNumber: text })}
                                    placeholder="ID Card Number"
                                    placeholderTextColor={themeStyles.placeholder}
                                    keyboardType="numeric"
                                />
                            </View>
                        </View>

                        {/* Phone Number */}
                        <View style={styles.inputGroup}>
                            <Text style={[styles.label, themeStyles.label]}>Phone Number</Text>
                            <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                <Phone size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                <TextInput
                                    style={[styles.input, themeStyles.input]}
                                    value={formData.phoneNumber}
                                    onChangeText={(text) => setFormData({ ...formData, phoneNumber: text })}
                                    placeholder="Phone Number"
                                    placeholderTextColor={themeStyles.placeholder}
                                    keyboardType="phone-pad"
                                />
                            </View>
                        </View>

                        {/* Address */}
                        <View style={styles.inputGroup}>
                            <Text style={[styles.label, themeStyles.label]}>Address</Text>
                            <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                <MapPin size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                <TextInput
                                    style={[styles.input, themeStyles.input]}
                                    value={formData.address}
                                    onChangeText={(text) => setFormData({ ...formData, address: text })}
                                    placeholder="Address"
                                    placeholderTextColor={themeStyles.placeholder}
                                />
                            </View>
                        </View>

                        {/* Date of Birth */}
                        <View style={styles.inputGroup}>
                            <Text style={[styles.label, themeStyles.label]}>Date of Birth</Text>
                            <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                                <Calendar size={20} color={themeStyles.icon} style={styles.inputIcon} />
                                <TextInput
                                    style={[styles.input, themeStyles.input]}
                                    value={formData.dateOfBirth}
                                    onChangeText={(text) => setFormData({ ...formData, dateOfBirth: text })}
                                    placeholder="YYYY-MM-DD"
                                    placeholderTextColor={themeStyles.placeholder}
                                />
                            </View>
                        </View>

                        <Button
                            title="Save Changes"
                            onPress={handleSave}
                            isLoading={isLoading}
                            buttonStyle={styles.saveButton}
                            leftIcon={<Save size={20} color="#fff" />}
                        />

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
        marginTop: Layout.spacing.md,
    },
});
