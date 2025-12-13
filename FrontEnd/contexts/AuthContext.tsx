import React, { createContext, useState, useContext, useEffect } from 'react';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
// import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
// import { LoginManager, AccessToken } from 'react-native-fbsdk-next';
import { authService } from '@/services/api';
import { DBUser } from '@/types/schema';
import { getUserStatusLabel } from '@/utils/formatting';


type User = {
  id: string;
  email: string;
  name: string;
  token?: string;
  phoneNumber?: string;
  address?: string;
  idCardNumber?: string;
  dateOfBirth?: string;
  status?: boolean;
  statusLabel?: string;
  notificationsEnabled?: boolean;
};

type AuthContextType = {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string, otp: string, additionalData?: any) => Promise<void>;
  signOut: () => Promise<void>;
  googleSignIn: () => Promise<void>;
  facebookSignIn: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
  isProfileComplete: (user: User) => boolean;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: false,
  error: null,
  signIn: async () => { },
  signUp: async () => { },
  signOut: async () => { },
  googleSignIn: async () => { },
  facebookSignIn: async () => { },
  clearError: () => { },
  setUser: () => { },
  isProfileComplete: () => false,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on load
  useEffect(() => {
    /*
    GoogleSignin.configure({
      webClientId: '802152854534-4g42qdqklbdogi1dego7qm01ib4ufk5f.apps.googleusercontent.com', // Get this from Google Cloud Console
      offlineAccess: true,
    });
    */
    const loadUserFromStorage = async () => {
      try {
        const userJson = await AsyncStorage.getItem('user');
        if (userJson) {
          setUser(JSON.parse(userJson));
        }
      } catch (e) {
        console.error('Failed to load user from storage', e);
      } finally {
        setIsLoading(false);
      }
    };

    loadUserFromStorage();
  }, []);

  const isProfileComplete = (user: User) => {
    return !!(user.phoneNumber && user.address && user.idCardNumber && user.dateOfBirth);
  };

  const signIn = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await authService.login(email, password);
      console.log('📦 Login response data:', JSON.stringify(data, null, 2));
      const appUser: User = {
        id: data.user.UserID.toString(),
        name: data.user.UserName || data.user.UserIDCardName, // ✅ Fix: Handle UserName from Login/Register
        email: data.user.UserEmail || data.user.Email, // ✅ Fix: Handle UserEmail from Login/Register
        token: data.access_token,
        phoneNumber: data.user.PhoneNumber,
        address: data.user.Address,
        idCardNumber: data.user.UserIDCardNumber ? data.user.UserIDCardNumber.toString() : undefined, // Backend 'UserIDCardNumber'
        dateOfBirth: data.user.DateOfBirth,
        status: data.user.UserStatus,
        statusLabel: getUserStatusLabel(data.user.UserStatus),
        notificationsEnabled: data.user.IsNotificationsEnabled
      };
      console.log('👤 Created appUser object:', JSON.stringify(appUser, null, 2));
      await AsyncStorage.setItem('user', JSON.stringify(appUser));
      setUser(appUser);

      if (!isProfileComplete(appUser)) {
        router.replace('/complete-profile');
      } else {
        router.replace('/(tabs)');
      }
    } catch (e: any) {
      if (e.response) {
        // Server responded with a status code (e.g., 400, 401, 500)
        setError(`Server: ${e.response?.data?.detail || e.response?.data?.message || 'Login failed'}`);
      } else if (e.request) {
        // Request made but no response (Network Error)
        setError('Network Error: Could not connect to server. Check your IP/Wi-Fi.');
      } else {
        setError(`Error: ${e.message || 'Login failed'}`);
      }
      console.error('Login error', e);
    } finally {
      setIsLoading(false);
    }
  };

  const signUp = async (name: string, email: string, password: string, otp: string, additionalData?: any) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await authService.register(name, email, password, otp, additionalData);
      console.log('📦 Signup response data:', JSON.stringify(data, null, 2));

      // Ensure we map ALL fields returned from backend
      const appUser: User = {
        id: data.user.UserID.toString(),
        name: data.user.UserName || data.user.UserIDCardName, // ✅ Fix: Handle UserName
        email: data.user.UserEmail || data.user.Email, // ✅ Fix: Handle UserEmail
        token: data.access_token,
        phoneNumber: data.user.PhoneNumber ?? additionalData?.phoneNumber,
        address: data.user.Address ?? additionalData?.address,
        idCardNumber: data.user.UserIDCardNumber ? data.user.UserIDCardNumber.toString() : additionalData?.idCardNumber,
        dateOfBirth: data.user.DateOfBirth ?? additionalData?.dateOfBirth,
        status: data.user.UserStatus,
        statusLabel: getUserStatusLabel(data.user.UserStatus || true), // specific assumption for new user
        notificationsEnabled: data.user.IsNotificationsEnabled
      };

      console.log('👤 Created signup appUser:', JSON.stringify(appUser, null, 2));
      await AsyncStorage.setItem('user', JSON.stringify(appUser));

      // Update state directly
      setUser(appUser);

      console.log('✅ User data saved to AsyncStorage and AuthContext');

      if (!isProfileComplete(appUser)) {
        router.replace('/complete-profile');
      } else {
        router.replace('/(tabs)');
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || e.response?.data?.message || 'Registration failed');
      console.error('Registration error', e);
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      // await GoogleSignin.signOut();
      // LoginManager.logOut();
      await AsyncStorage.removeItem('user');
      setUser(null);
      router.replace('/login');
    } catch (e) {
      console.error('Error signing out', e);
    } finally {
      setIsLoading(false);
    }
  };

  const googleSignIn = async () => {
    console.log("Google Auth temporarily disabled");
    alert("Google Auth is temporarily disabled (Missing google-services.json)");
    /*
    setIsLoading(true);
    setError(null);
    try {
      await GoogleSignin.hasPlayServices();
      const response = await GoogleSignin.signIn();

      if (response.data?.idToken) {
        // Verify with Backend
        const data = await authService.googleLogin(response.data.idToken);

        const appUser: User = {
          id: data.user.UserID.toString(),
          name: data.user.UserName,
          email: data.user.UserEmail,
          token: data.token
        };

        await AsyncStorage.setItem('user', JSON.stringify(appUser));
        setUser(appUser);
        
        if (!isProfileComplete(appUser)) {
          router.replace('/complete-profile');
        } else {
          router.replace('/(tabs)');
        }
      } else {
        throw new Error('No ID token returned from Google');
      }
    } catch (error: any) {
      if (error.code === statusCodes.SIGN_IN_CANCELLED) {
        // user cancelled the login flow
      } else if (error.code === statusCodes.IN_PROGRESS) {
        // operation (e.g. sign in) is in progress already
      } else if (error.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        // play services not available or outdated
        setError('Play Services not available');
      } else {
        setError('Google Sign-In failed');
        console.error(error);
      }
    } finally {
      setIsLoading(false);
    }
    */
  };

  const facebookSignIn = async () => {
    console.log("Facebook Auth temporarily disabled");
    alert("Facebook Auth is temporarily disabled");
    /*
    setIsLoading(true);
    setError(null);
    try {
      const result = await LoginManager.logInWithPermissions(['public_profile', 'email']);
      if (result.isCancelled) {
        throw new Error('User cancelled the login process');
      }

      const data = await AccessToken.getCurrentAccessToken();
      if (!data) {
        throw new Error('Something went wrong obtaining access token');
      }

      // Verify with Backend
      const backendResponse = await authService.facebookLogin(data.accessToken);

      const appUser: User = {
        id: backendResponse.user.UserID.toString(),
        name: backendResponse.user.UserName,
        email: backendResponse.user.UserEmail,
        token: backendResponse.token
      };

      await AsyncStorage.setItem('user', JSON.stringify(appUser));
      setUser(appUser);
      
      if (!isProfileComplete(appUser)) {
        router.replace('/complete-profile');
      } else {
        router.replace('/(tabs)');
      }
    } catch (e) {
      setError('Facebook Sign-In failed');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
    */
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        error,
        signIn,
        signUp,
        signOut,
        googleSignIn,
        facebookSignIn,
        clearError,
        setUser,
        isProfileComplete,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};