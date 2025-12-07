import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Keyboard,
  TouchableWithoutFeedback,
  TouchableOpacity,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Server, Globe, User, Lock, CheckCircle, CreditCard, DollarSign, Hash } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useAccounts } from '@/contexts/AccountsContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';
import Input from '@/components/Input';
import Button from '@/components/Button';

export default function AddAccountScreen() {
  const { addAccount, error, clearError } = useAccounts();
  const { colors } = useTheme();

  const [formData, setFormData] = useState({
    loginNumber: '',
    password: '',
    server: '',
    riskPercentage: '1.00',
    strategy: 'All' as 'All' | 'FVG + Trend' | 'Voting',
  });

  const [isLoading, setIsLoading] = useState(false);

  const handleAddAccount = async () => {
    if (!formData.loginNumber || !formData.password || !formData.server) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    const riskValue = parseFloat(formData.riskPercentage);
    if (isNaN(riskValue) || riskValue < 0 || riskValue > 10) {
      Alert.alert('Error', 'Risk percentage must be between 0% and 10%');
      return;
    }

    setIsLoading(true);
    try {
      const result = await addAccount({
        loginNumber: formData.loginNumber,
        password: formData.password,
        server: formData.server,
        riskPercentage: riskValue,
        strategy: formData.strategy,
      });

      if (result.success) {
        Alert.alert(
          'Success!',
          `${result.message}\n\n` +
          `Balance: $${result.mt5Info?.balance || 0}\n` +
          `Leverage: 1:${result.mt5Info?.leverage || 0}\n` +
          `Server: ${result.mt5Info?.server || formData.server}`,
          [{ text: 'OK', onPress: () => router.back() }]
        );
      } else {
        Alert.alert('Verification Failed', result.message);
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to add account');
    } finally {
      setIsLoading(false);
    }
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    label: { color: colors.text },
    inputContainer: {
      backgroundColor: colors.card,
      borderColor: colors.border,
    },
    input: { color: colors.text },
    placeholder: colors.placeholder,
    icon: colors.placeholder,
    typeButton: {
      borderColor: colors.border,
      backgroundColor: colors.card,
    },
    typeButtonActive: {
      borderColor: colors.primary,
      backgroundColor: 'rgba(91, 72, 210, 0.1)',
    },
    typeText: { color: colors.placeholder },
    typeTextActive: { color: colors.primary },
  };

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.header}>
            <HeadingText style={[styles.title, themeStyles.title]}>Add New Account</HeadingText>
          </View>

          <View style={styles.form}>
            {/* Login Number */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Login Number *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <Hash size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.loginNumber}
                  onChangeText={(text) => setFormData({ ...formData, loginNumber: text })}
                  placeholder="Account Login Number"
                  placeholderTextColor={themeStyles.placeholder}
                  keyboardType="numeric"
                />
              </View>
            </View>

            {/* Password */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Password *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <Lock size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.password}
                  onChangeText={(text) => setFormData({ ...formData, password: text })}
                  placeholder="Account Password"
                  placeholderTextColor={themeStyles.placeholder}
                  secureTextEntry
                />
              </View>
            </View>

            {/* Server */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Server *</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <Server size={20} color={themeStyles.icon} style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.server}
                  onChangeText={(text) => setFormData({ ...formData, server: text })}
                  placeholder="e.g. MetaQuotes-Demo"
                  placeholderTextColor={themeStyles.placeholder}
                />
              </View>
            </View>

            {/* Risk Percentage */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Risk Percentage (Max 10%)</BodyText>
              <View style={[styles.inputContainer, themeStyles.inputContainer]}>
                <BodyText style={[styles.percentIcon, { color: themeStyles.icon }]}>%</BodyText>
                <TextInput
                  style={[styles.input, themeStyles.input]}
                  value={formData.riskPercentage}
                  onChangeText={(text) => setFormData({ ...formData, riskPercentage: text })}
                  placeholder="1.00"
                  placeholderTextColor={themeStyles.placeholder}
                  keyboardType="decimal-pad"
                />
              </View>
              <BodyText style={[styles.helperText, { color: colors.placeholder }]}>
                Maximum risk per trade (0% - 10%)
              </BodyText>
            </View>

            {/* Trading Strategy */}
            <View style={styles.inputGroup}>
              <BodyText style={[styles.label, themeStyles.label]}>Trading Strategy</BodyText>
              <View style={styles.strategyContainer}>
                {(['All', 'FVG + Trend', 'Voting'] as const).map((strategy) => (
                  <TouchableOpacity
                    key={strategy}
                    style={[
                      styles.strategyButton,
                      themeStyles.typeButton,
                      formData.strategy === strategy && themeStyles.typeButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, strategy })}
                  >
                    <BodyText
                      style={[
                        styles.typeText,
                        themeStyles.typeText,
                        formData.strategy === strategy && themeStyles.typeTextActive,
                      ]}
                    >
                      {strategy}
                    </BodyText>
                    {formData.strategy === strategy && (
                      <CheckCircle
                        size={18}
                        color={colors.primary}
                        style={styles.checkIcon}
                      />
                    )}
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <Button
              title="Verify & Create Account"
              onPress={handleAddAccount}
              isLoading={isLoading}
              buttonStyle={styles.createButton}
            />
          </View>
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
    padding: Layout.spacing.lg,
    paddingBottom: Layout.spacing.xxl,
  },
  header: {
    marginBottom: Layout.spacing.xl,
  },
  title: {
    fontSize: 24,
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
  percentIcon: {
    fontSize: 18,
    fontWeight: '600',
    marginRight: Layout.spacing.sm,
  },
  helperText: {
    fontSize: 12,
    marginLeft: 4,
    marginTop: 4,
  },
  strategyContainer: {
    gap: Layout.spacing.sm,
  },
  strategyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    borderRadius: Layout.borderRadius.md,
    borderWidth: 1,
    position: 'relative',
  },
  typeContainer: {
    flexDirection: 'row',
    gap: Layout.spacing.md,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    borderRadius: Layout.borderRadius.md,
    borderWidth: 1,
    position: 'relative',
  },
  typeText: {
    fontSize: 16,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
  },
  checkIcon: {
    position: 'absolute',
    right: 10,
  },
  createButton: {
    marginTop: Layout.spacing.md,
  },
});