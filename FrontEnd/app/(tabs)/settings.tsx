import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  User,
  Settings as SettingsIcon,
  Bell,
  Shield,
  CreditCard,
  HelpCircle,
  LogOut,
  ChevronRight,
  Moon,
  Sun
} from 'lucide-react-native';
import { router } from 'expo-router';

import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText } from '@/components/StyledText';

export default function SettingsScreen() {
  const { signOut, user } = useAuth();
  const { theme, toggleTheme, colors } = useTheme();

  const [pushNotifications, setPushNotifications] = useState(true);
  const [biometricEnabled, setBiometricEnabled] = useState(false);

  const handleLogout = () => {
    Alert.alert(
      'Log Out',
      'Are you sure you want to log out?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: async () => {
            await signOut();
            router.replace('/login');
          },
        },
      ]
    );
  };

  const togglePushNotifications = (value: boolean) => {
    setPushNotifications(value);
    // In a real app, we would call an API to update user preferences
    // or register/unregister the device token
  };

  // Dynamic styles
  const themeStyles = {
    container: { backgroundColor: colors.surface },
    title: { color: colors.text },
    sectionTitle: { color: colors.placeholder },
    card: { backgroundColor: colors.card },
    settingItem: { borderBottomColor: colors.border },
    settingText: { color: colors.text },
    settingSubtext: { color: colors.placeholder },
    logoutText: { color: colors.negative },
    versionText: { color: colors.placeholder },
  };

  const SettingItem = ({
    icon,
    title,
    subtitle,
    onPress,
    showChevron = true,
    rightElement,
    isDestructive = false
  }: {
    icon: React.ReactNode,
    title: string,
    subtitle?: string,
    onPress?: () => void,
    showChevron?: boolean,
    rightElement?: React.ReactNode,
    isDestructive?: boolean
  }) => (
    <TouchableOpacity
      style={[styles.settingItem, themeStyles.settingItem]}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingLeft}>
        <View style={styles.iconContainer}>
          {icon}
        </View>
        <View style={styles.textContainer}>
          <BodyText style={[
            styles.settingTitle,
            themeStyles.settingText,
            isDestructive && themeStyles.logoutText
          ]}>
            {title}
          </BodyText>
          {subtitle && (
            <BodyText style={[styles.settingSubtitle, themeStyles.settingSubtext]}>
              {subtitle}
            </BodyText>
          )}
        </View>
      </View>

      {rightElement ? (
        rightElement
      ) : showChevron ? (
        <ChevronRight size={20} color={colors.placeholder} />
      ) : null}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <HeadingText style={[styles.title, themeStyles.title]}>Settings</HeadingText>
        </View>

        <View style={styles.profileSection}>
          <View style={[styles.avatarContainer, { backgroundColor: colors.primary }]}>
            <HeadingText style={styles.avatarText}>
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </HeadingText>
          </View>
          <View style={styles.profileInfo}>
            <HeadingText style={[styles.profileName, themeStyles.settingText]}>
              {user?.name || 'User'}
            </HeadingText>
            <BodyText style={[styles.profileEmail, themeStyles.settingSubtext]}>
              {user?.email || 'user@example.com'}
            </BodyText>
          </View>
          <TouchableOpacity
            style={[styles.editProfileButton, { backgroundColor: colors.card }]}
            onPress={() => router.push('/edit-profile')}
          >
            <BodyText style={{ color: colors.primary, fontSize: 14 }}>Edit</BodyText>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <BodyText style={[styles.sectionTitle, themeStyles.sectionTitle]}>Preferences</BodyText>
          <View style={[styles.card, themeStyles.card]}>
            <SettingItem
              icon={<Moon size={20} color={colors.text} />}
              title="Dark Mode"
              showChevron={false}
              rightElement={
                <Switch
                  value={theme === 'dark'}
                  onValueChange={toggleTheme}
                  trackColor={{ false: '#767577', true: colors.primary }}
                  thumbColor="#f4f3f4"
                />
              }
            />
            <SettingItem
              icon={<Bell size={20} color={colors.text} />}
              title="Push Notifications"
              subtitle="Receive alerts when app is closed"
              showChevron={false}
              rightElement={
                <Switch
                  value={pushNotifications}
                  onValueChange={togglePushNotifications}
                  trackColor={{ false: '#767577', true: colors.primary }}
                  thumbColor="#f4f3f4"
                />
              }
            />
          </View>
        </View>

        <View style={styles.section}>
          <BodyText style={[styles.sectionTitle, themeStyles.sectionTitle]}>Account</BodyText>
          <View style={[styles.card, themeStyles.card]}>
            <SettingItem
              icon={<User size={20} color={colors.text} />}
              title="Personal Information"
              onPress={() => router.push('/edit-profile')}
            />
            <SettingItem
              icon={<Shield size={20} color={colors.text} />}
              title="Security"
              subtitle="Password, Biometric"
              onPress={() => router.push('/security')}
            />
            <SettingItem
              icon={<CreditCard size={20} color={colors.text} />}
              title="Payment Methods"
              onPress={() => { }}
            />
          </View>
        </View>

        <View style={styles.section}>
          <BodyText style={[styles.sectionTitle, themeStyles.sectionTitle]}>Support</BodyText>
          <View style={[styles.card, themeStyles.card]}>
            <SettingItem
              icon={<HelpCircle size={20} color={colors.text} />}
              title="Help Center"
              onPress={() => { }}
            />
            <SettingItem
              icon={<SettingsIcon size={20} color={colors.text} />}
              title="About"
              onPress={() => { }}
            />
          </View>
        </View>

        <View style={styles.section}>
          <View style={[styles.card, themeStyles.card]}>
            <SettingItem
              icon={<LogOut size={20} color={colors.negative} />}
              title="Log Out"
              isDestructive
              onPress={handleLogout}
              showChevron={false}
            />
          </View>
        </View>

        <View style={styles.footer}>
          <BodyText style={[styles.versionText, themeStyles.versionText]}>
            Version 1.0.0
          </BodyText>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Layout.spacing.md,
    paddingBottom: Layout.spacing.xxl,
  },
  header: {
    marginBottom: Layout.spacing.lg,
  },
  title: {
    fontSize: 28,
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Layout.spacing.xl,
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Layout.spacing.md,
  },
  avatarText: {
    color: '#fff',
    fontSize: 24,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
  },
  editProfileButton: {
    paddingHorizontal: Layout.spacing.md,
    paddingVertical: Layout.spacing.xs,
    borderRadius: Layout.borderRadius.round,
  },
  section: {
    marginBottom: Layout.spacing.lg,
  },
  sectionTitle: {
    fontSize: 14,
    marginBottom: Layout.spacing.sm,
    marginLeft: Layout.spacing.xs,
    textTransform: 'uppercase',
    fontWeight: '600',
    fontFamily: 'Inter-Medium',
  },
  card: {
    borderRadius: Layout.borderRadius.lg,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: Layout.spacing.md,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Layout.spacing.md,
  },
  textContainer: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  footer: {
    marginTop: Layout.spacing.lg,
    alignItems: 'center',
  },
  versionText: {
    fontSize: 12,
    textAlign: 'center',
    marginBottom: Layout.spacing.xl,
  },
});