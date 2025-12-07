import { Text, TextProps } from 'react-native';
import { useTheme } from '@/contexts/ThemeContext';

export function MonoText(props: TextProps) {
  const { colors } = useTheme();
  return <Text {...props} style={[{ color: colors.text, fontFamily: 'Inter-Regular' }, props.style]} />;
}

export function HeadingText(props: TextProps) {
  const { colors } = useTheme();
  return <Text {...props} style={[{ color: colors.text, fontFamily: 'Inter-Bold', fontWeight: '700' }, props.style]} />;
}

export function SubheadingText(props: TextProps) {
  const { colors } = useTheme();
  return <Text {...props} style={[{ color: colors.text, fontFamily: 'Inter-Medium', fontWeight: '500' }, props.style]} />;
}

export function BodyText(props: TextProps) {
  const { colors } = useTheme();
  return <Text {...props} style={[{ color: colors.text, fontFamily: 'Inter-Regular' }, props.style]} />;
}

export function SmallText(props: TextProps) {
  const { colors } = useTheme();
  return <Text {...props} style={[{ color: colors.text, fontFamily: 'Inter-Regular', fontSize: 12 }, props.style]} />;
}