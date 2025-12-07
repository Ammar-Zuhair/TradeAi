# إعداد الاتصال السحابي (MetaApi)

لقد تم تعديل النظام ليدعم الاتصال السحابي عبر **MetaApi** لتجاوز قيود الاستضافة.

## الخطوات المطلوبة:

1. **إنشاء حساب MetaApi:**
   - قم بالتسجيل في [MetaApi Cloud](https://app.metaapi.cloud).
   - أنشئ حساباً جديداً واربط حساب التداول الخاص بك (MetaTrader 5).

2. **الحصول على البيانات:**
   - **Token**: من صفحة "API Tokens" في لوحة التحكم.
   - **Account ID**: من صفحة "Accounts"، انسخ الـ ID الخاص بحسابك.

3. **تحديث ملف `.env`:**
   افتح ملف `.env` وأضف البيانات التالية:

   ```env
   # إعدادات الاتصال السحابي
   CONNECTION_MODE=CLOUD
   METAAPI_TOKEN=your_token_here
   METAAPI_ACCOUNT_ID=your_account_id_here
   ```

   > **ملاحظة:** للعودة للوضع المحلي (Local)، غير `CONNECTION_MODE` إلى `LOCAL`.

4. **تثبيت المكتبات الجديدة:**
   ```bash
   pip install -r requirements.txt
   ```

## الملفات التي تم تعديلها:

- `mt5_adapter.py` (ملف جديد: المحول الذكي)
- `env_loader.py` (إضافة إعدادات السحابة)
- `requirements.txt` (إضافة مكتبة metaapi)
- `Run_System.py` (تعديل لاستخدام المحول)
- `getDataAndVoting.py` (تعديل لاستخدام المحول)
- `detect_FVG/Run_FVG.py` (تعديل لاستخدام المحول)
- `PredictNextPrice/Run_PricePredictor.py` (تعديل لاستخدام المحول)
