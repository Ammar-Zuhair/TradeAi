import axios from 'axios';
import { Platform } from 'react-native';

// ---------------------------------------------------------------------------
// 🔧 MANUAL CONFIGURATION
// ---------------------------------------------------------------------------
// Replace this with your computer's IP address
// How to find it:
// 1. Open Command Prompt (cmd)
// 2. Type 'ipconfig'
// 3. Look for "IPv4 Address" (e.g., 192.168.1.5)
const SERVER_IP = '10.134.17.95';
const SERVER_PORT = '3000';
// ---------------------------------------------------------------------------

const getApiUrl = () => {
    // For Android Emulator, use special IP
    if (Platform.OS === 'android') {
        // If you are using the standard Android Emulator, use 10.0.2.2
        // If you are using a physical device, use the SERVER_IP above
        // return `http://10.0.2.2:${SERVER_PORT}/api`; // Uncomment for Emulator
        return `http://${SERVER_IP}:${SERVER_PORT}/api`; // For Physical Device
    }

    // For iOS Simulator or Web
    return `http://localhost:${SERVER_PORT}/api`;
};

const API_URL = getApiUrl();

console.log('🔌 API Service Initialized');
console.log('🔗 Target API URL:', API_URL);

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,
});

// Add request interceptor for logging
api.interceptors.request.use(request => {
    console.log('🚀 Starting Request:', request.method?.toUpperCase(), request.url);
    return request;
});

api.interceptors.response.use(
    response => {
        console.log('✅ Response Received:', response.status, response.config.url);
        return response;
    },
    error => {
        console.log('❌ Request Failed:', error.message);
        if (error.response) {
            console.log('   Status:', error.response.status);
            console.log('   Data:', error.response.data);
        } else if (error.request) {
            console.log('   No response received from server');
            console.log('   Possible causes:');
            console.log('   1. Wrong IP address in api.ts');
            console.log('   2. Phone and Computer not on same Wi-Fi');
            console.log('   3. Windows Firewall blocking port 3000');
            console.log('   4. Backend server is not running');
        }
        return Promise.reject(error);
    }
);

export const authService = {
    login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password });
        return response.data;
    },
    register: async (name: string, email: string, password: string, otp: string, additionalData?: any) => {
        const response = await api.post('/auth/register', { name, email, password, otp, ...additionalData });
        return response.data;
    },
    sendOTP: async (email: string, name: string) => {
        const response = await api.post('/auth/send-otp', { email, name });
        return response.data;
    },
    verifyOTP: async (email: string, otp: string) => {
        const response = await api.post('/auth/verify-otp', { email, otp });
        return response.data;
    },
    requestPasswordReset: async (email: string) => {
        const response = await api.post('/auth/forgot-password', { email });
        return response.data;
    },
    resetPassword: async (email: string, otp: string, newPassword: string) => {
        const response = await api.post('/auth/reset-password', { email, otp, newPassword });
        return response.data;
    },
    googleLogin: async (idToken: string) => {
        const response = await api.post('/auth/google', { idToken });
        return response.data;
    },
    facebookLogin: async (accessToken: string) => {
        const response = await api.post('/auth/facebook', { accessToken });
        return response.data;
    },
    updateProfile: async (token: string, data: any) => {
        const response = await api.put('/auth/profile', data, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },
    changePassword: async (token: string, currentPassword: string, newPassword: string) => {
        const response = await api.put('/auth/change-password', null, {
            params: {
                current_password: currentPassword,
                new_password: newPassword
            },
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },
    deleteAccount: async (token: string) => {
        const response = await api.delete('/auth/delete-account', {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },
};

export const userService = {
    getUser: async (id: number) => {
        const response = await api.get(`/users/${id}`);
        return response.data;
    },
    updateUser: async (id: number, data: any) => {
        const response = await api.put(`/users/${id}`, data);
        return response.data;
    },
};

export const accountService = {
    getAccounts: async (token: string, userId?: number) => {
        const url = userId ? `/accounts?userID=${userId}` : '/accounts';
        const response = await api.get(url, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },

    createAccount: async (token: string, data: {
        UserID: number;
        AccountLoginNumber: number;
        AccountLoginPassword: string;
        AccountLoginServer: string;
        RiskPercentage?: number;
        TradingStrategy?: 'All' | 'FVG + Trend' | 'Voting';
    }) => {
        const response = await api.post('/accounts', data, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },

    updateAccount: async (token: string, accountId: number, data: any) => {
        const response = await api.put(`/accounts/${accountId}`, data, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },

    deleteAccount: async (token: string, accountId: number) => {
        const response = await api.delete(`/accounts/${accountId}`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },
};

export const tradeService = {
    getTrades: async (token: string, accountId?: number) => {
        const url = accountId ? `/trades?accountID=${accountId}` : '/trades';
        const response = await api.get(url, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },

    getTrade: async (token: string, tradeId: number) => {
        const response = await api.get(`/trades/${tradeId}`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    },

    closeAllTrades: async (token: string, accountId: number) => {
        const response = await api.post(`/trades/close-all/${accountId}`, {}, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    }
};

export default api;
