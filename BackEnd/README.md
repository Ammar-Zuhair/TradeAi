# Trading App Backend - Python FastAPI

Backend للتطبيق التداول مبني على Python FastAPI مع دعم كامل لنماذج الذكاء الاصطناعي.

## 🚀 المميزات

- ✅ **FastAPI Framework** - أداء عالي وسرعة فائقة
- ✅ **PostgreSQL Database** - قاعدة بيانات قوية وموثوقة
- ✅ **JWT Authentication** - نظام مصادقة آمن
- ✅ **OTP Verification** - التحقق عبر OTP
- ✅ **Google & Facebook OAuth** - تسجيل دخول عبر Google و Facebook
- ✅ **Password Encryption** - تشفير كلمات المرور
- ✅ **AI Integration** - دعم كامل لنماذج الذكاء الاصطناعي
- ✅ **Auto Scheduler** - تشغيل تلقائي للنماذج كل 15 دقيقة
- ✅ **Auto Documentation** - توثيق تلقائي للـ API (Swagger UI)

## 📋 المتطلبات

- Python 3.8 أو أحدث
- PostgreSQL
- pip (Python package manager)

## 🔧 التثبيت

### 1. إنشاء بيئة افتراضية (Virtual Environment)

```bash
cd d:\project\BackEnd
python -m venv venv
```

### 2. تفعيل البيئة الافتراضية

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. تثبيت المكتبات المطلوبة

```bash
pip install -r requirements.txt
```

### 4. إنشاء جداول قاعدة البيانات

```bash
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## ▶️ تشغيل السيرفر

### Development Mode (مع Auto-reload)

```bash
uvicorn main:app --reload --port 3000
```
uvicorn main:app --reload --host 0.0.0.0 --port 3000
### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 3000 --workers 4
```

## 📖 التوثيق التلقائي

بعد تشغيل السيرفر، يمكنك الوصول إلى:

- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/send-otp` - إرسال OTP
- `POST /api/auth/verify-otp` - التحقق من OTP
- `POST /api/auth/register` - تسجيل مستخدم جديد
- `POST /api/auth/login` - تسجيل الدخول
- `POST /api/auth/forgot-password` - طلب إعادة تعيين كلمة المرور
- `POST /api/auth/reset-password` - إعادة تعيين كلمة المرور
- `POST /api/auth/google` - تسجيل دخول عبر Google
- `POST /api/auth/facebook` - تسجيل دخول عبر Facebook

### Users
- `POST /api/users` - إنشاء مستخدم
- `GET /api/users` - الحصول على جميع المستخدمين
- `GET /api/users/{id}` - الحصول على مستخدم محدد
- `PUT /api/users/{id}` - تحديث مستخدم
- `DELETE /api/users/{id}` - حذف مستخدم

### Accounts
- `POST /api/accounts` - إنشاء حساب تداول
- `GET /api/accounts` - الحصول على جميع الحسابات
- `GET /api/accounts/{id}` - الحصول على حساب محدد
- `PUT /api/accounts/{id}` - تحديث حساب
- `DELETE /api/accounts/{id}` - حذف حساب

### Trades
- `POST /api/trades` - إنشاء صفقة
- `GET /api/trades` - الحصول على جميع الصفقات
- `GET /api/trades/{id}` - الحصول على صفقة محددة
- `PUT /api/trades/{id}` - تحديث صفقة

### Transactions
- `POST /api/transactions` - إنشاء معاملة
- `GET /api/transactions` - الحصول على جميع المعاملات
- `GET /api/transactions/{id}` - الحصول على معاملة محددة

### AI Recommendations
- `GET /api/ai/recommendations` - الحصول على توصيات الذكاء الاصطناعي
- `POST /api/ai/trigger-analysis` - تشغيل التحليل يدوياً
- `GET /api/ai/status` - حالة نظام الذكاء الاصطناعي

## 🤖 دمج نماذج الذكاء الاصطناعي

### 1. ضع ملفات النماذج الخاصة بك

ضع ملفات نماذج الذكاء الاصطناعي في المجلد:
```
d:\project\BackEnd\ai_integration\
```

### 2. قم بتعديل ملف `model_runner.py`

افتح الملف `ai_integration/model_runner.py` وقم بتحديث الكود:

```python
class AIModelRunner:
    def __init__(self):
        # قم بتحميل نماذجك هنا
        self.model = load_model('path/to/your/model.h5')
    
    def run_analysis(self):
        # قم بتشغيل نماذجك هنا
        predictions = self.model.predict(data)
        return predictions
```

### 3. الجدولة التلقائية

النظام يقوم تلقائياً بتشغيل نماذج الذكاء الاصطناعي كل **15 دقيقة**.

يمكنك تغيير الفترة الزمنية في ملف `main.py`:

```python
ai_scheduler.start(run_ai_models, interval_minutes=15)  # غير الرقم حسب الحاجة
```

## 🗂️ هيكل المشروع

```
BackEnd/
├── main.py                 # نقطة البداية الرئيسية
├── database.py             # إعدادات قاعدة البيانات
├── requirements.txt        # المكتبات المطلوبة
├── .env                    # متغيرات البيئة
├── models/                 # نماذج قاعدة البيانات
│   ├── user.py
│   ├── account.py
│   ├── trade.py
│   └── transaction.py
├── schemas/                # Pydantic schemas للتحقق
│   ├── user.py
│   ├── account.py
│   ├── trade.py
│   ├── transaction.py
│   └── auth.py
├── routers/                # API endpoints
│   ├── auth.py
│   ├── users.py
│   ├── accounts.py
│   ├── trades.py
│   ├── transactions.py
│   └── ai_recommendations.py
├── utils/                  # أدوات مساعدة
│   ├── security.py         # التشفير والمصادقة
│   └── dependencies.py     # FastAPI dependencies
└── ai_integration/         # دمج الذكاء الاصطناعي
    ├── model_runner.py     # تشغيل النماذج
    └── scheduler.py        # الجدولة التلقائية
```

## 🔐 الأمان

- كلمات المرور مشفرة باستخدام **bcrypt**
- بيانات اعتماد الوسيط مشفرة باستخدام **AES-256-CBC**
- JWT tokens للمصادقة
- OTP verification للتسجيل وإعادة تعيين كلمة المرور

## 🧪 الاختبار

### اختبار الاتصال بقاعدة البيانات

```bash
python -c "from database import engine; print('✅ Connected!' if engine else '❌ Failed')"
```

### اختبار API

استخدم Swagger UI على:
```
http://localhost:3000/docs
```

## 📝 ملاحظات مهمة

1. **ملف .env**: تأكد من أن جميع المتغيرات موجودة في ملف `.env`
2. **قاعدة البيانات**: يجب أن تكون PostgreSQL قيد التشغيل
3. **نماذج الذكاء الاصطناعي**: ضع نماذجك في `ai_integration/model_runner.py`
4. **OTP**: حالياً يتم طباعة OTP في console (للتطوير فقط)
   - في الإنتاج، استخدم خدمة بريد إلكتروني

## 🆚 الفرق عن Express.js

| الميزة | Express.js (القديم) | FastAPI (الجديد) |
|--------|-------------------|------------------|
| اللغة | JavaScript | Python |
| الأداء | جيد | ممتاز |
| التوثيق | يدوي | تلقائي (Swagger) |
| دعم AI | صعب | سهل جداً |
| Type Safety | لا | نعم (Pydantic) |
| Async | نعم | نعم (أفضل) |

## 🔄 الترحيل من Express.js

جميع الوظائف من Express.js موجودة في FastAPI:
- ✅ جميع API endpoints
- ✅ المصادقة والأمان
- ✅ قاعدة البيانات
- ✅ OTP verification
- ✅ OAuth (Google & Facebook)
- ➕ دعم الذكاء الاصطناعي (جديد!)
- ➕ جدولة تلقائية (جديد!)

## 🐛 استكشاف الأخطاء

### خطأ في الاتصال بقاعدة البيانات
```bash
# تحقق من أن PostgreSQL يعمل
# تحقق من بيانات الاتصال في .env
```

### خطأ في تثبيت المكتبات
```bash
# قم بترقية pip
python -m pip install --upgrade pip
# أعد تثبيت المكتبات
pip install -r requirements.txt
```

### Port مستخدم بالفعل
```bash
# غير PORT في .env
# أو أوقف العملية التي تستخدم Port 3000
```

## 📞 الدعم

إذا واجهت أي مشاكل، تحقق من:
1. Logs في terminal
2. Swagger UI للأخطاء في API
3. ملف `.env` للتأكد من الإعدادات

---

**تم بناؤه بواسطة FastAPI ❤️**
