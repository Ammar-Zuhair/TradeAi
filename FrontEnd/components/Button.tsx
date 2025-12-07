import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacityProps,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: ButtonVariant;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  buttonStyle?: ViewStyle;
  textStyle?: TextStyle;
}

export default function Button({
  title,
  variant = 'primary',
  isLoading = false,
  leftIcon,
  rightIcon,
  buttonStyle,
  textStyle,
  disabled,
  ...props
}: ButtonProps) {
  const { colors } = useTheme();

  const getButtonStyles = () => {
    switch (variant) {
      case 'primary':
        return { backgroundColor: colors.primary };
      case 'secondary':
        return { backgroundColor: colors.card }; // Secondary often uses card color or a lighter primary
      case 'outline':
        return {
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderColor: colors.primary,
        };
      case 'ghost':
        return { backgroundColor: 'transparent' };
      case 'danger':
        return { backgroundColor: colors.negative };
      default:
        return { backgroundColor: colors.primary };
    }
  };

  const getTextStyles = () => {
    switch (variant) {
      case 'primary':
        return { color: '#fff' };
      case 'secondary':
        return { color: colors.text };
      case 'outline':
        return { color: colors.primary };
      case 'ghost':
        return { color: colors.primary };
      case 'danger':
        return { color: '#fff' };
      default:
        return { color: '#fff' };
    }
  };

  return (
    <TouchableOpacity
      style={[
        styles.button,
        getButtonStyles(),
        disabled && { backgroundColor: colors.border, borderColor: colors.border },
        buttonStyle,
      ]}
      disabled={disabled || isLoading}
      activeOpacity={0.8}
      {...props}
    >
      {isLoading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'outline' || variant === 'ghost' ? colors.primary : '#fff'}
        />
      ) : (
        <>
          {leftIcon && <>{leftIcon}</>}
          <Text
            style={[
              styles.text,
              getTextStyles(),
              disabled && { color: colors.placeholder },
              leftIcon ? { marginLeft: Layout.spacing.sm } : undefined,
              rightIcon ? { marginRight: Layout.spacing.sm } : undefined,
              textStyle,
            ]}
          >
            {title}
          </Text>
          {rightIcon && <>{rightIcon}</>}
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Layout.spacing.md,
    paddingHorizontal: Layout.spacing.lg,
    borderRadius: Layout.borderRadius.md,
    minHeight: 48,
  },
  text: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
});