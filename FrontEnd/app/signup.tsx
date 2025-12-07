import React, { useState } from 'react';
import DatePickerModal from '@/components/DatePickerModal';
import { View, StyleSheet, TouchableOpacity, ScrollView, Text, TextInput, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, router } from 'expo-router';
import { User, Mail, Lock, CreditCard, Phone, MapPin, Calendar, Square, CheckSquare } from 'lucide-react-native';
import Animated, { FadeInUp, FadeInDown } from 'react-native-reanimated';

import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/api';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import Button from '@/components/Button';

export default function SignupScreen() {
  const { signUp, isLoading: authLoading } = useAuth();
  const { colors } = useTheme();
  const [isLoading, setIsLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    idCardNumber: '',
    phoneNumber: '',
    address: '',
    dateOfBirth: '',
  });

  const [agreements, setAgreements] = useState({
    privacy: false,
    terms: false,
    eula: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showDatePicker, setShowDatePicker] = useState(false);

  const handleDateChange = (date: string) => {
    setFormData({ ...formData, dateOfBirth: date });
    setShowDatePicker(false);
  };

  const calculateAge = (dateString: string) => {
    const today = new Date();
    const birthDate = new Date(dateString);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name) newErrors.name = 'Full name is required';
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Email is invalid';

    if (!formData.password) newErrors.password = 'Password is required';
    else if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.idCardNumber) {
      newErrors.idCardNumber = 'ID Card Number is required';
    } else if (!/^\d+$/.test(formData.idCardNumber)) {
      newErrors.idCardNumber = 'ID Card must be numeric';
    }

    if (!formData.phoneNumber) {
      newErrors.phoneNumber = 'Phone Number is required';
    } else if (!/^\d+$/.test(formData.phoneNumber)) {
      newErrors.phoneNumber = 'Phone Number must be numeric';
    }

    if (!formData.dateOfBirth) {
      newErrors.dateOfBirth = 'Date of Birth is required';
    } else {
      // Simple regex for YYYY-MM-DD
      if (!/^\d{4}-\d{2}-\d{2}$/.test(formData.dateOfBirth)) {
        newErrors.dateOfBirth = 'Format must be YYYY-MM-DD';
      } else {
        const age = calculateAge(formData.dateOfBirth);
        if (isNaN(age)) {
          newErrors.dateOfBirth = 'Invalid date';
        } else if (age < 18) {
          newErrors.dateOfBirth = 'You must be at least 18 years old to register.';
        }
      }
    }

    if (!agreements.privacy) newErrors.privacy = 'Required';
    if (!agreements.terms) newErrors.terms = 'Required';
    if (!agreements.eula) newErrors.eula = 'Required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignup = async () => {
    if (!validate()) {
      if (!agreements.privacy || !agreements.terms || !agreements.eula) {
        Alert.alert('Agreements Required', 'Please accept all terms and conditions to proceed.');
      }
      return;
    }

    setIsLoading(true);
    try {
      await authService.sendOTP(formData.email, formData.name);

      router.push({
        pathname: '/verify-email',
        params: {
          name: formData.name,
          email: formData.email,
          password: formData.password,
          idCardNumber: formData.idCardNumber,
          phoneNumber: formData.phoneNumber,
          address: formData.address,
          dateOfBirth: formData.dateOfBirth
        }
      });
    } catch (error: any) {
      Alert.alert('Signup Failed', error.response?.data?.message || 'Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    subtitle: { color: colors.placeholder },
    inputContainer: {
      backgroundColor: colors.card,
      borderColor: colors.border,
    },
    input: { color: colors.text },
    placeholder: colors.placeholder,
    icon: colors.placeholder,
    link: { color: colors.primary },
    errorText: { color: colors.negative },
    checkboxText: { color: colors.text },
  };

  const toggleAgreement = (key: keyof typeof agreements) => {
    setAgreements(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View entering={FadeInUp.delay(200).springify()} style={styles.header}>
            <Text style={[styles.title, themeStyles.title]}>Create Account</Text>
            <Text style={[styles.subtitle, themeStyles.subtitle]}>Sign up to start trading</Text>
          </Animated.View>

          <Animated.View entering={FadeInDown.delay(400).springify()} style={styles.form}>
            {/* Full Name */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.name ? { borderColor: colors.negative } : null]}>
                <User size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Full Name (as on ID)"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.name}
                  onChangeText={(text) => setFormData({ ...formData, name: text })}
                />
              </View>
              {errors.name && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.name}</Text>}
            </View>

            {/* ID Card Number */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.idCardNumber ? { borderColor: colors.negative } : null]}>
                <CreditCard size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="ID Card Number"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.idCardNumber}
                  onChangeText={(text) => setFormData({ ...formData, idCardNumber: text })}
                  keyboardType="numeric"
                />
              </View>
              {errors.idCardNumber && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.idCardNumber}</Text>}
            </View>

            {/* Email */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.email ? { borderColor: colors.negative } : null]}>
                <Mail size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Email Address"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.email}
                  onChangeText={(text) => setFormData({ ...formData, email: text })}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
              {errors.email && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.email}</Text>}
            </View>

            {/* Phone Number */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.phoneNumber ? { borderColor: colors.negative } : null]}>
                <Phone size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Phone Number"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.phoneNumber}
                  onChangeText={(text) => setFormData({ ...formData, phoneNumber: text })}
                  keyboardType="phone-pad"
                />
              </View>
              {errors.phoneNumber && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.phoneNumber}</Text>}
            </View>

            {/* Address */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <MapPin size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Address"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.address}
                  onChangeText={(text) => setFormData({ ...formData, address: text })}
                />
              </View>
            </View>

            {/* Date of Birth */}
            <View style={styles.inputGroup}>
              <TouchableOpacity onPress={() => setShowDatePicker(true)}>
                <View style={[styles.inputContainer, themeStyles.inputContainer, errors.dateOfBirth ? { borderColor: colors.negative } : null]}>
                  <Calendar size={20} color={themeStyles.icon} style={styles.inputIcon} />
                  <Text style={[styles.input, themeStyles.input, { textAlignVertical: 'center', paddingTop: 12 }, !formData.dateOfBirth && { color: themeStyles.placeholder }]}>
                    {formData.dateOfBirth || "Date of Birth (YYYY-MM-DD)"}
                  </Text>
                </View>
              </TouchableOpacity>
              {errors.dateOfBirth && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.dateOfBirth}</Text>}
              <DatePickerModal
                visible={showDatePicker}
                onClose={() => setShowDatePicker(false)}
                onSelect={handleDateChange}
                initialDate={formData.dateOfBirth}
              />
            </View>

            {/* Password */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.password ? { borderColor: colors.negative } : null]}>
                <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Password"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.password}
                  onChangeText={(text) => setFormData({ ...formData, password: text })}
                  secureTextEntry
                />
              </View>
              {errors.password && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.password}</Text>}
            </View>

            {/* Confirm Password */}
            <View style={styles.inputGroup}>
              <View style={[styles.inputContainer, themeStyles.inputContainer, errors.confirmPassword ? { borderColor: colors.negative } : null]}>
                <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  placeholder="Confirm Password"
                  placeholderTextColor={themeStyles.placeholder}
                  value={formData.confirmPassword}
                  onChangeText={(text) => setFormData({ ...formData, confirmPassword: text })}
                  secureTextEntry
                />
              </View>
              {errors.confirmPassword && <Text style={[styles.errorText, themeStyles.errorText]}>{errors.confirmPassword}</Text>}
            </View>

            {/* Agreements */}
            <View style={styles.agreementsContainer}>
              <TouchableOpacity style={styles.checkboxRow} onPress={() => toggleAgreement('privacy')}>
                {agreements.privacy ? (
                  <CheckSquare size={24} color={colors.primary} />
                ) : (
                  <Square size={24} color={errors.privacy ? colors.negative : colors.placeholder} />
                )}
                <Text style={[styles.checkboxLabel, themeStyles.checkboxText]}>I agree to the Privacy Policy</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.checkboxRow} onPress={() => toggleAgreement('terms')}>
                {agreements.terms ? (
                  <CheckSquare size={24} color={colors.primary} />
                ) : (
                  <Square size={24} color={errors.terms ? colors.negative : colors.placeholder} />
                )}
                <Text style={[styles.checkboxLabel, themeStyles.checkboxText]}>I agree to the Terms of Service</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.checkboxRow} onPress={() => toggleAgreement('eula')}>
                {agreements.eula ? (
                  <CheckSquare size={24} color={colors.primary} />
                ) : (
                  <Square size={24} color={errors.eula ? colors.negative : colors.placeholder} />
                )}
                <Text style={[styles.checkboxLabel, themeStyles.checkboxText]}>I agree to the End User License Agreement</Text>
              </TouchableOpacity>
            </View>

            <Button
              title="Sign Up"
              onPress={handleSignup}
              isLoading={isLoading}
              buttonStyle={styles.signupButton}
            />

            <View style={styles.footer}>
              <Text style={[styles.footerText, themeStyles.subtitle]}>Already have an account? </Text>
              <Link href="/login" asChild>
                <TouchableOpacity>
                  <Text style={[styles.link, themeStyles.link]}>Log In</Text>
                </TouchableOpacity>
              </Link>
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
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: Layout.spacing.lg,
  },
  header: {
    marginTop: Layout.spacing.xl,
    marginBottom: Layout.spacing.xxl,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    fontFamily: 'Inter-Bold',
    marginBottom: Layout.spacing.xs,
  },
  subtitle: {
    fontSize: 16,
  },
  form: {
    gap: Layout.spacing.md,
  },
  inputGroup: {
    marginBottom: Layout.spacing.sm,
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
  errorText: {
    fontSize: 12,
    marginTop: 4,
    marginLeft: 4,
  },
  signupButton: {
    marginTop: Layout.spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: Layout.spacing.lg,
    marginBottom: Layout.spacing.xl,
  },
  footerText: {
    fontSize: 14,
  },
  link: {
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  agreementsContainer: {
    gap: Layout.spacing.sm,
    marginVertical: Layout.spacing.sm,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Layout.spacing.sm,
  },
  checkboxLabel: {
    fontSize: 14,
    flex: 1,
  },
});