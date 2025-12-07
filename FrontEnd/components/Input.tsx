import React, { useState } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  Text,
  TouchableOpacity,
  TextInputProps,
  ViewStyle,
} from 'react-native';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { Eye, EyeOff } from 'lucide-react-native';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  containerStyle?: ViewStyle;
  isPassword?: boolean;
}

export default function Input({
  label,
  error,
  leftIcon,
  rightIcon,
  containerStyle,
  isPassword = false,
  ...props
}: InputProps) {
  const { colors } = useTheme();
  const [isFocused, setIsFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Dynamic styles
  const themeStyles = {
    label: { color: colors.text },
    inputContainer: {
      borderColor: colors.border,
      backgroundColor: colors.surface,
    },
    inputContainerFocused: {
      borderColor: colors.primary,
    },
    inputContainerError: {
      borderColor: colors.negative,
    },
    input: {
      color: colors.text,
    },
    errorText: {
      color: colors.negative,
    },
  };

  return (
    <View style={[styles.container, containerStyle]}>
      {label && <Text style={[styles.label, themeStyles.label]}>{label}</Text>}

      <View style={[
        styles.inputContainer,
        themeStyles.inputContainer,
        isFocused && themeStyles.inputContainerFocused,
        error && themeStyles.inputContainerError,
      ]}>
        {leftIcon && <View style={styles.leftIconContainer}>{leftIcon}</View>}

        <TextInput
          style={[
            styles.input,
            themeStyles.input,
            leftIcon ? styles.inputWithLeftIcon : undefined,
            (rightIcon || isPassword) ? styles.inputWithRightIcon : undefined,
          ]}
          placeholderTextColor={colors.placeholder}
          selectionColor={colors.primary}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          secureTextEntry={isPassword && !showPassword}
          {...props}
        />

        {isPassword ? (
          <TouchableOpacity
            style={styles.rightIconContainer}
            onPress={() => setShowPassword(!showPassword)}
          >
            {showPassword ?
              <EyeOff size={20} color={colors.placeholder} /> :
              <Eye size={20} color={colors.placeholder} />
            }
          </TouchableOpacity>
        ) : rightIcon ? (
          <View style={styles.rightIconContainer}>{rightIcon}</View>
        ) : null}
      </View>

      {error && <Text style={[styles.errorText, themeStyles.errorText]}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: Layout.spacing.md,
  },
  label: {
    marginBottom: Layout.spacing.xs,
    fontSize: 14,
    fontWeight: '500',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: Layout.borderRadius.md,
  },
  input: {
    flex: 1,
    height: 48,
    paddingHorizontal: Layout.spacing.md,
    fontSize: 16,
  },
  inputWithLeftIcon: {
    paddingLeft: 8,
  },
  inputWithRightIcon: {
    paddingRight: 8,
  },
  leftIconContainer: {
    paddingLeft: Layout.spacing.md,
  },
  rightIconContainer: {
    paddingRight: Layout.spacing.md,
  },
  errorText: {
    marginTop: Layout.spacing.xs,
    fontSize: 12,
  },
});