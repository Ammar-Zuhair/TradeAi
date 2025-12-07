# Frontend API Integration Guide

## ✅ Changes Made to Frontend

All frontend API calls have been updated to match the new Python FastAPI backend.

---

## 📝 Updated Files

### 1. [`services/api.ts`](file:///d:/project/FrontEnd/services/api.ts)

#### API URL Configuration
- **Old**: Fixed IP `http://192.168.1.100:3000/api`
- **New**: Dynamic URL based on platform
  - iOS/Web: `http://localhost:3000/api`
  - Android Emulator: `http://10.0.2.2:3000/api`

#### Updated Endpoints

**sendOTP**
```typescript
// Old
sendOTP: async (email: string)

// New
sendOTP: async (email: string, name: string)
```

**register**
```typescript
// Old
register: async (name: string, email: string, password: string, verificationToken: string)

// New
register: async (name: string, email: string, password: string, otp: string)
```

**resetPassword**
```typescript
// Old
resetPassword: async (token: string, newPassword: string)

// New
resetPassword: async (email: string, otp: string, newPassword: string)
```

**googleLogin**
```typescript
// Old
googleLogin: async (token: string) => api.post('/auth/google', { token })

// New
googleLogin: async (idToken: string) => api.post('/auth/google', { idToken })
```

**facebookLogin**
```typescript
// Old
facebookLogin: async (token: string) => api.post('/auth/facebook', { token })

// New
facebookLogin: async (accessToken: string) => api.post('/auth/facebook', { accessToken })
```

---

### 2. [`app/signup.tsx`](file:///d:/project/FrontEnd/app/signup.tsx)

**Updated sendOTP call**
```typescript
// Old
await authService.sendOTP(email);

// New
await authService.sendOTP(email, name);
```

---

### 3. [`app/verify-email.tsx`](file:///d:/project/FrontEnd/app/verify-email.tsx)

**Simplified registration flow**
```typescript
// Old - Two-step process
const verifyResponse = await authService.verifyOTP(email, code);
const registerResponse = await authService.register(name, email, password, verifyResponse.verificationToken);

// New - Single step (backend verifies OTP during registration)
const registerResponse = await authService.register(name, email, password, code);
```

**Updated token field**
```typescript
// Old
token: registerResponse.token

// New
token: registerResponse.access_token
```

**Updated resend OTP**
```typescript
// Old
await authService.sendOTP(email);

// New
await authService.sendOTP(email, name);
```

---

### 4. [`contexts/AuthContext.tsx`](file:///d:/project/FrontEnd/contexts/AuthContext.tsx)

**Updated signIn function**
```typescript
// Old
token: data.token

// New
token: data.access_token
```

**Updated error handling**
```typescript
// Old
setError(e.response?.data?.message || 'Login failed');

// New
setError(e.response?.data?.detail || e.response?.data?.message || 'Login failed');
```

**Updated signUp signature**
```typescript
// Old
signUp: (name: string, email: string, password: string, verificationToken: string) => Promise<void>

// New
signUp: (name: string, email: string, password: string, otp: string) => Promise<void>
```

---

## 🔄 Backend Response Structure Changes

### Login Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "UserID": 1,
    "UserName": "John Doe",
    "UserEmail": "john@example.com",
    "UserStatus": "Active"
  }
}
```

### Register Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "UserID": 1,
    "UserName": "John Doe",
    "UserEmail": "john@example.com",
    "UserStatus": "Active"
  }
}
```

### Error Response
```json
{
  "detail": "Invalid email or password"
}
```

---

## 🧪 Testing Checklist

- [x] API URL updated to use localhost
- [x] sendOTP includes name parameter
- [x] register uses otp instead of verificationToken
- [x] Login response uses access_token
- [x] Register response uses access_token
- [x] Error handling includes detail field
- [x] Password reset uses email + otp
- [x] OAuth endpoints use correct parameter names

---

## 🚀 How to Test

### 1. Start Backend
```bash
cd d:\project\BackEnd
venv\Scripts\activate
uvicorn main:app --reload --port 3000
```

### 2. Start Frontend
```bash
cd d:\project\FrontEnd
npx expo start
```

### 3. Test Registration Flow
1. Open app and go to signup
2. Enter name, email, password
3. Click "Create Account"
4. Check backend console for OTP
5. Enter OTP in verification screen
6. Should redirect to main app

### 4. Test Login Flow
1. Go to login screen
2. Enter email and password
3. Click "Sign In"
4. Should redirect to main app

---

## 📌 Important Notes

### Platform-Specific URLs

**iOS Simulator / Web**
- Use `http://localhost:3000/api`
- Works directly

**Android Emulator**
- Use `http://10.0.2.2:3000/api`
- 10.0.2.2 is the special IP for Android emulator to access host machine

**Physical Device**
- Need to use your computer's IP address
- Example: `http://192.168.1.100:3000/api`
- Make sure device and computer are on same network

### OTP in Development

Currently, OTP is printed in the backend console:
```
OTP for user@example.com: 123456
```

In production, you should:
1. Remove the OTP from response
2. Send OTP via email service (SendGrid, AWS SES, etc.)
3. Update backend `routers/auth.py` to integrate email service

---

## ✅ All Changes Complete

The frontend is now fully compatible with the Python FastAPI backend!
