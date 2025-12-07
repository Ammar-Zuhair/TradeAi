import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Platform, TouchableOpacity, Alert } from 'react-native';
import { router } from 'expo-router';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Calendar, MapPin, Phone, CreditCard, ArrowRight } from 'lucide-react-native';

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Input from '@/components/Input';
import Button from '@/components/Button';
import { authService } from '@/services/api';

export default function CompleteProfileScreen() {
    const { user, setUser } = useAuth();
    const { colors } = useTheme();
    const [isLoading, setIsLoading] = useState(false);

    const [phoneNumber, setPhoneNumber] = useState(user?.phoneNumber || '');
    const [address, setAddress] = useState(user?.address || '');
    const [idCardNumber, setIdCardNumber] = useState(user?.idCardNumber || '');
    const [dateOfBirth, setDateOfBirth] = useState<Date | undefined>(
        user?.dateOfBirth ? new Date(user.dateOfBirth) : undefined
    );
    const [showDatePicker, setShowDatePicker] = useState(false);

    const [errors, setErrors] = useState({
        phoneNumber: '',
        address: '',
        idCardNumber: '',
        dateOfBirth: '',
    });

    const validateForm = () => {
        let isValid = true;
        const newErrors = {
            phoneNumber: '',
            address: '',
            idCardNumber: '',
            dateOfBirth: '',
        };

        if (!phoneNumber.trim()) {
            newErrors.phoneNumber = 'Phone number is required';
            isValid = false;
        }

        if (!address.trim()) {
            newErrors.address = 'Address is required';
            isValid = false;
        }

        if (!idCardNumber.trim()) {
            newErrors.idCardNumber = 'ID Card Number is required';
            isValid = false;
        }

        if (!dateOfBirth) {
            newErrors.dateOfBirth = 'Date of Birth is required';
            isValid = false;
        } else {
            // Check if 18+
            const today = new Date();
            const age = today.getFullYear() - dateOfBirth.getFullYear();
            const m = today.getMonth() - dateOfBirth.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < dateOfBirth.getDate())) {
                if (age - 1 < 18) {
                    newErrors.dateOfBirth = 'You must be at least 18 years old';
                    isValid = false;
                }
            } else {
                if (age < 18) {
                    newErrors.dateOfBirth = 'You must be at least 18 years old';
                    isValid = false;
                }
            }
        }

        setErrors(newErrors);
        return isValid;
    };

    const handleDateChange = (event: any, selectedDate?: Date) => {
        setShowDatePicker(Platform.OS === 'ios');
        if (selectedDate) {
            setDateOfBirth(selectedDate);
        }
    };

    const handleSubmit = async () => {
        if (!validateForm()) return;
        if (!user?.token) {
            Alert.alert('Error', 'User session not found. Please login again.');
            router.replace('/login');
            return;
        }

        setIsLoading(true);
        try {
            const formattedDate = dateOfBirth?.toISOString().split('T')[0];

            const updateData = {
                PhoneNumber: phoneNumber,
                Address: address,
                UserIDCardrNumber: parseInt(idCardNumber), // Backend expects integer
                DateOfBirth: formattedDate,
            };

            console.log('Updating profile with:', updateData);

            const updatedUser = await authService.updateProfile(user.token, updateData);

            // Update local user context
            const newUserData = {
                ...user,
                phoneNumber: updatedUser.PhoneNumber,
                address: updatedUser.Address,
                idCardNumber: updatedUser.UserIDCardrNumber?.toString(),
                dateOfBirth: updatedUser.DateOfBirth,
            };

            setUser(newUserData);

            // Navigate to main app
            router.replace('/(tabs)');

        } catch (error: any) {
            console.error('Profile update failed:', error);
            Alert.alert('Update Failed', error.response?.data?.detail || 'Failed to update profile');
        } finally {
            setIsLoading(false);
        }
    };

    const themeStyles = {
        container: { backgroundColor: colors.surface },
        title: { color: colors.text },
        subtitle: { color: colors.placeholder },
        dateText: { color: dateOfBirth ? colors.text : colors.placeholder },
        dateButton: {
            borderColor: errors.dateOfBirth ? colors.negative : colors.border,
            backgroundColor: colors.background
        },
        errorText: { color: colors.negative },
    };

    return (
        <ScrollView
            style={[styles.container, themeStyles.container]}
            contentContainerStyle={styles.contentContainer}
        >
            <View style={styles.header}>
                <HeadingText style={[styles.title, themeStyles.title]}>Complete Profile</HeadingText>
                <BodyText style={[styles.subtitle, themeStyles.subtitle]}>
                    Please provide the following details to complete your registration.
                </BodyText>
            </View>

            <View style={styles.form}>
                <Input
                    label="Phone Number"
                    placeholder="Enter your phone number"
                    value={phoneNumber}
                    onChangeText={setPhoneNumber}
                    error={errors.phoneNumber}
                    keyboardType="phone-pad"
                    leftIcon={<Phone size={20} color={colors.placeholder} />}
                />

                <Input
                    label="Address"
                    placeholder="Enter your address"
                    value={address}
                    onChangeText={setAddress}
                    error={errors.address}
                    leftIcon={<MapPin size={20} color={colors.placeholder} />}
                />

                <Input
                    label="ID Card Number"
                    placeholder="Enter your ID number"
                    value={idCardNumber}
                    onChangeText={setIdCardNumber}
                    error={errors.idCardNumber}
                    keyboardType="numeric"
                    leftIcon={<CreditCard size={20} color={colors.placeholder} />}
                />

                <View style={styles.dateContainer}>
                    <BodyText style={styles.label}>Date of Birth</BodyText>
                    <TouchableOpacity
                        style={[styles.dateButton, themeStyles.dateButton]}
                        onPress={() => setShowDatePicker(true)}
                    >
                        <Calendar size={20} color={colors.placeholder} style={styles.dateIcon} />
                        <BodyText style={themeStyles.dateText}>
                            {dateOfBirth ? dateOfBirth.toLocaleDateString() : 'Select Date of Birth'}
                        </BodyText>
                    </TouchableOpacity>
                    {errors.dateOfBirth ? (
                        <BodyText style={[styles.errorText, themeStyles.errorText]}>{errors.dateOfBirth}</BodyText>
                    ) : null}
                </View>

                {showDatePicker && (
                    <DateTimePicker
                        value={dateOfBirth || new Date()}
                        mode="date"
                        display="default"
                        onChange={handleDateChange}
                        maximumDate={new Date()}
                    />
                )}

                <Button
                    title="Complete Registration"
                    onPress={handleSubmit}
                    isLoading={isLoading}
                    style={styles.button}
                    rightIcon={<ArrowRight size={20} color="#fff" />}
                />
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    contentContainer: {
        padding: Layout.spacing.lg,
        paddingTop: 60,
    },
    header: {
        marginBottom: Layout.spacing.xl,
    },
    title: {
        fontSize: 28,
        marginBottom: Layout.spacing.xs,
    },
    subtitle: {
        fontSize: 16,
    },
    form: {
        gap: Layout.spacing.md,
    },
    dateContainer: {
        marginBottom: Layout.spacing.md,
    },
    label: {
        fontSize: 14,
        fontWeight: '500',
        marginBottom: 8,
        marginLeft: 4,
    },
    dateButton: {
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1,
        borderRadius: Layout.borderRadius.md,
        padding: Layout.spacing.md,
        height: 50,
    },
    dateIcon: {
        marginRight: Layout.spacing.sm,
    },
    errorText: {
        fontSize: 12,
        marginTop: 4,
        marginLeft: 4,
    },
    button: {
        marginTop: Layout.spacing.md,
    },
});
