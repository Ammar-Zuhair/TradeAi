import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ArrowLeft, Bell, CheckCircle, AlertTriangle, Info, X } from 'lucide-react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { useTheme } from '@/contexts/ThemeContext';
import Layout from '@/constants/Layout';
import { HeadingText, BodyText, SubheadingText } from '@/components/StyledText';

type NotificationType = 'success' | 'warning' | 'info' | 'error';

interface Notification {
    id: string;
    type: NotificationType;
    title: string;
    message: string;
    time: string;
    read: boolean;
}

const MOCK_NOTIFICATIONS: Notification[] = [
    {
        id: '1',
        type: 'success',
        title: 'Trade Executed',
        message: 'Buy order for EURUSD was successfully executed at 1.0850.',
        time: '2 mins ago',
        read: false,
    },
    {
        id: '2',
        type: 'warning',
        title: 'Margin Call Warning',
        message: 'Your margin level is below 100%. Please deposit funds or close positions.',
        time: '1 hour ago',
        read: false,
    },
    {
        id: '3',
        type: 'info',
        title: 'Market Update',
        message: 'US Non-Farm Payrolls data will be released in 30 minutes.',
        time: '3 hours ago',
        read: true,
    },
    {
        id: '4',
        type: 'success',
        title: 'Deposit Confirmed',
        message: 'Your deposit of $1,000.00 has been credited to your account.',
        time: 'Yesterday',
        read: true,
    },
    {
        id: '5',
        type: 'info',
        title: 'System Maintenance',
        message: 'Scheduled maintenance will take place on Sunday from 02:00 to 04:00 UTC.',
        time: '2 days ago',
        read: true,
    },
];

export default function NotificationsScreen() {
    const { colors } = useTheme();
    const [notifications, setNotifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = async () => {
        setRefreshing(true);
        // Simulate API refresh
        await new Promise(resolve => setTimeout(resolve, 1500));
        setRefreshing(false);
    };

    const markAllAsRead = () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    };

    const deleteNotification = (id: string) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const getIcon = (type: NotificationType) => {
        switch (type) {
            case 'success':
                return <CheckCircle size={24} color={colors.positive} />;
            case 'warning':
                return <AlertTriangle size={24} color="#FFB155" />; // Warning color
            case 'error':
                return <AlertTriangle size={24} color={colors.negative} />;
            case 'info':
            default:
                return <Info size={24} color={colors.primary} />;
        }
    };

    // Dynamic styles
    const themeStyles = {
        container: { backgroundColor: colors.surface },
        headerTitle: { color: colors.text },
        card: { backgroundColor: colors.card },
        title: { color: colors.text },
        message: { color: colors.placeholder },
        time: { color: colors.placeholder },
        unreadDot: { backgroundColor: colors.primary },
        emptyText: { color: colors.placeholder },
    };

    return (
        <SafeAreaView style={[styles.container, themeStyles.container]} edges={['top']}>
            <View style={styles.header}>
                <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => router.back()}
                >
                    <ArrowLeft size={24} color={colors.text} />
                </TouchableOpacity>
                <HeadingText style={[styles.headerTitle, themeStyles.headerTitle]}>Notifications</HeadingText>
                <TouchableOpacity onPress={markAllAsRead}>
                    <BodyText style={{ color: colors.primary }}>Mark all read</BodyText>
                </TouchableOpacity>
            </View>

            <ScrollView
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
                refreshControl={
                    <RefreshControl
                        refreshing={refreshing}
                        onRefresh={onRefresh}
                        tintColor={colors.primary}
                        colors={[colors.primary]}
                    />
                }
            >
                {notifications.length === 0 ? (
                    <View style={styles.emptyContainer}>
                        <Bell size={48} color={colors.placeholder} style={{ opacity: 0.5 }} />
                        <BodyText style={[styles.emptyText, themeStyles.emptyText]}>No notifications yet</BodyText>
                    </View>
                ) : (
                    notifications.map((item, index) => (
                        <Animated.View
                            key={item.id}
                            entering={FadeInDown.delay(index * 100).springify()}
                            style={[styles.notificationCard, themeStyles.card]}
                        >
                            <View style={styles.iconContainer}>
                                {getIcon(item.type)}
                            </View>

                            <View style={styles.contentContainer}>
                                <View style={styles.cardHeader}>
                                    <SubheadingText style={[styles.title, themeStyles.title]}>{item.title}</SubheadingText>
                                    {!item.read && <View style={[styles.unreadDot, themeStyles.unreadDot]} />}
                                </View>
                                <BodyText style={[styles.message, themeStyles.message]} numberOfLines={2}>
                                    {item.message}
                                </BodyText>
                                <BodyText style={[styles.time, themeStyles.time]}>{item.time}</BodyText>
                            </View>

                            <TouchableOpacity
                                style={styles.deleteButton}
                                onPress={() => deleteNotification(item.id)}
                            >
                                <X size={16} color={colors.placeholder} />
                            </TouchableOpacity>
                        </Animated.View>
                    ))
                )}
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: Layout.spacing.lg,
        paddingVertical: Layout.spacing.md,
    },
    backButton: {
        padding: Layout.spacing.xs,
        marginLeft: -Layout.spacing.xs,
    },
    headerTitle: {
        fontSize: 20,
    },
    scrollContent: {
        padding: Layout.spacing.md,
    },
    notificationCard: {
        flexDirection: 'row',
        borderRadius: Layout.borderRadius.lg,
        padding: Layout.spacing.md,
        marginBottom: Layout.spacing.md,
        alignItems: 'flex-start',
    },
    iconContainer: {
        marginRight: Layout.spacing.md,
        marginTop: 2,
    },
    contentContainer: {
        flex: 1,
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 4,
    },
    title: {
        fontSize: 16,
        fontWeight: '600',
    },
    unreadDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginLeft: 8,
    },
    message: {
        fontSize: 14,
        marginBottom: 8,
        lineHeight: 20,
    },
    time: {
        fontSize: 12,
    },
    deleteButton: {
        padding: 4,
        marginLeft: 8,
    },
    emptyContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: 100,
        gap: 16,
    },
    emptyText: {
        fontSize: 16,
    },
});
