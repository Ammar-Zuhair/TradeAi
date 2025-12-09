import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import api from './api';

Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

export async function registerForPushNotificationsAsync() {
    let token;

    if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#FF231F7C',
        });
    }

    if (Device.isDevice) {
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;
        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }
        if (finalStatus !== 'granted') {
            console.log('Failed to get push token for push notification!');
            return;
        }

        // Get Expo Push Token
        try {
            token = (await Notifications.getExpoPushTokenAsync({
                projectId: 'de080c35-84e9-4c92-b44a-2d7ad9c50644' // Optional, but good practice
            })).data;
            console.log("📲 Push Token:", token);
        } catch (e) {
            console.log("Error getting push token:", e);
        }
    } else {
        console.log('Must use physical device for Push Notifications');
    }

    return token;
}

export const notificationService = {
    updatePushToken: async (userToken: string, pushToken: string, enabled: boolean) => {
        try {
            await api.put('/auth/update-push-token', null, {
                params: {
                    token: pushToken,
                    enabled: enabled
                },
                headers: {
                    Authorization: `Bearer ${userToken}`
                }
            });
            console.log("✅ Push token updated on server");
        } catch (error) {
            console.error("❌ Failed to update push token on server:", error);
        }
    }
};
