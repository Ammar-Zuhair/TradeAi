# دليل إعداد الشبكة - TradeAI App

هذا الدليل يشرح كيفية إعداد الاتصال بين تطبيق React Native والـ Backend المحلي.

## 📋 المتطلبات الأساسية

### 1. الهاتف والكمبيوتر على نفس شبكة Wi-Fi
- تأكد أن كلاهما متصلان بنفس الراوتر
- لا تستخدم VPN على أي منهما

### 2. معرفة IP Address للكمبيوتر

#### على Windows:
```powershell
ipconfig
```
ابحث عن **IPv4 Address** تحت **Wireless LAN adapter Wi-Fi**

مثال: `192.168.1.5` أو `172.184.114.68`

#### على Mac/Linux:
```bash
ifconfig
```
ابحث عن **inet** تحت **en0** أو **wlan0**

---

## 🔧 إعداد التطبيق

### 1. تحديث عنوان السيرفر في `services/api.ts`

افتح الملف: `d:\project\FrontEnd\services\api.ts`

عدّل السطر 12:
```typescript
const SERVER_IP = '172.184.114.68'; // ضع IP الكمبيوتر هنا
const SERVER_PORT = '3000';
```

### 2. اختيار نوع الجهاز

#### للهاتف الحقيقي (Physical Device):
```typescript
return `http://${SERVER_IP}:${SERVER_PORT}/api`; // السطر 22
```

#### للـ Android Emulator:
```typescript
return `http://10.0.2.2:${SERVER_PORT}/api`; // السطر 21
```

---

## 🔥 إعداد Windows Firewall

### الطريقة السريعة (PowerShell كمسؤول):

```powershell
# السماح بالاتصالات الواردة على Port 3000
New-NetFirewallRule -DisplayName "TradeAI Backend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

### الطريقة اليدوية:

1. افتح **Windows Defender Firewall**
2. اضغط **Advanced settings**
3. اختر **Inbound Rules** → **New Rule**
4. اختر **Port** → **TCP** → **3000**
5. اختر **Allow the connection**
6. سمّها: `TradeAI Backend`

---

## 🏗️ بناء التطبيق

### Development Build (للتطوير):
```bash
cd d:\project\FrontEnd
npx expo run:android
```

### Release APK (مستقل تماماً):
```bash
cd d:\project\FrontEnd\android
.\gradlew assembleRelease
```

الملف سيكون في:
```
android\app\build\outputs\apk\release\app-release.apk
```

---

## 🧪 اختبار الاتصال

### 1. تشغيل Backend
```bash
cd d:\project\BackEnd
# تأكد من تشغيل السيرفر
```

### 2. اختبار من المتصفح
افتح في متصفح الهاتف:
```
http://172.184.114.68:3000/api/health
```

إذا ظهرت استجابة، الاتصال يعمل! ✅

### 3. فتح التطبيق
- افتح التطبيق على الهاتف
- راقب Console logs في Metro bundler
- حاول تسجيل الدخول أو التسجيل

---

## 🐛 استكشاف الأخطاء

### ❌ خطأ: "Network request failed"

**الحلول:**
1. تأكد من IP Address صحيح
2. تأكد من نفس شبكة Wi-Fi
3. تأكد من تشغيل Backend
4. افحص Windows Firewall
5. جرب إيقاف Antivirus مؤقتاً

### ❌ خطأ: "CLEARTEXT communication not permitted"

**الحل:**
تأكد من وجود الملفات التالية:
- `android/app/src/main/res/xml/network_security_config.xml`
- تحديث `AndroidManifest.xml` مع:
  ```xml
  android:usesCleartextTraffic="true"
  android:networkSecurityConfig="@xml/network_security_config"
  ```

### ❌ خطأ: "Connection timeout"

**الحلول:**
1. Backend قد يكون متوقف
2. Port 3000 محجوب بواسطة Firewall
3. IP Address خاطئ
4. الهاتف على شبكة مختلفة

---

## 🚀 للإنتاج (Production)

عند نشر التطبيق للمستخدمين:

### 1. استخدم HTTPS
```typescript
const API_URL = 'https://yourdomain.com/api';
```

### 2. احصل على شهادة SSL
- استخدم Let's Encrypt (مجاني)
- أو شهادة SSL مدفوعة

### 3. انشر Backend على سيرفر عام
- AWS EC2
- DigitalOcean
- Azure
- Google Cloud

### 4. عدّل Network Security Config
في `network_security_config.xml`:
```xml
<base-config cleartextTrafficPermitted="false">
    <trust-anchors>
        <certificates src="system" />
    </trust-anchors>
</base-config>

<domain-config>
    <domain includeSubdomains="true">yourdomain.com</domain>
</domain-config>
```

---

## 📱 معلومات إضافية

### الفرق بين Development و Production:

| الميزة | Development | Production |
|--------|-------------|------------|
| Protocol | HTTP | HTTPS |
| Server | Local (192.168.x.x) | Public Domain |
| Security | Cleartext Allowed | Encrypted Only |
| Certificate | None | SSL Required |
| Firewall | Manual Config | Cloud Provider |

### أوامر مفيدة:

```bash
# عرض الأجهزة المتصلة
adb devices

# عرض logs من الهاتف
adb logcat | grep -i "tradeai"

# تثبيت APK مباشرة
adb install app-release.apk

# حذف التطبيق
adb uninstall com.anonymous.boltexponativewind
```

---

## 💡 نصائح

1. **احفظ IP Address**: قد يتغير عند إعادة تشغيل الراوتر
2. **استخدم Static IP**: في إعدادات الراوتر لتثبيت IP الكمبيوتر
3. **Port Forwarding**: إذا أردت الوصول من خارج الشبكة المحلية
4. **Testing**: اختبر دائماً على Release build قبل النشر

---

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من Console logs
2. استخدم `adb logcat` لرؤية أخطاء Android
3. تأكد من تشغيل Backend بدون أخطاء
4. جرب من متصفح الهاتف أولاً
