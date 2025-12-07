import React from 'react';
import { 
  TouchableOpacity, 
  Text, 
  StyleSheet, 
  TouchableOpacityProps 
} from 'react-native';
import Colors from '@/constants/Colors';

interface TextButtonProps extends TouchableOpacityProps {
  title: string;
  color?: string;
}

export default function TextButton({ 
  title, 
  color = Colors.trading.primary,
  ...props 
}: TextButtonProps) {
  return (
    <TouchableOpacity style={styles.container} {...props}>
      <Text style={[styles.text, { color }]}>{title}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 8,
  },
  text: {
    fontSize: 14,
    fontWeight: '500',
  },
});