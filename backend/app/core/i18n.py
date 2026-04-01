"""
AXONHIS Backend Internationalization (i18n) Module
Provides localized API responses, validation messages, and system notifications.
"""

from typing import Optional, Dict
import json
import os

# ─── Translation Store ────────────────────────────────────────────────────
_translations: Dict[str, Dict[str, str]] = {}
_fallback_locale = "en"

# Backend-specific messages (validation errors, system notifications, etc.)
BACKEND_TRANSLATIONS = {
    "en": {
        "auth.invalid_credentials": "Invalid email or password",
        "auth.token_expired": "Session expired. Please login again.",
        "auth.unauthorized": "You are not authorized to perform this action",
        "patient.created": "Patient registered successfully",
        "patient.updated": "Patient updated successfully",
        "patient.not_found": "Patient not found",
        "patient.duplicate_found": "A patient with similar details already exists",
        "ipd.admission_created": "IPD admission request created successfully",
        "ipd.bed_allocated": "Bed allocated successfully",
        "ipd.bed_unavailable": "Cannot allocate bed. Request must be approved and bed must be available.",
        "ipd.discharge_completed": "Patient discharged successfully",
        "ipd.billing.charge_added": "Service charge added to bill",
        "ipd.billing.deposit_collected": "Advance deposit collected successfully",
        "ipd.billing.insurance_filed": "Insurance claim filed successfully",
        "ipd.billing.insurance_approved": "Insurance claim approved",
        "ipd.billing.payment_processed": "Payment processed successfully",
        "ipd.billing.bill_settled": "Bill fully settled",
        "pharmacy.dispensed": "Medication dispensed successfully",
        "pharmacy.stock_low": "Stock level below reorder threshold",
        "pharmacy.out_of_stock": "Item out of stock",
        "lab.order_placed": "Lab order placed successfully",
        "lab.result_available": "Lab result available for review",
        "lab.result_validated": "Lab result validated and released",
        "blood_bank.donor_registered": "Blood donor registered successfully",
        "blood_bank.unit_collected": "Blood unit collected and logged",
        "blood_bank.crossmatch_passed": "Crossmatch test passed",
        "encounter.created": "Encounter created successfully",
        "encounter.completed": "Encounter completed",
        "ward.bed_created": "Bed created successfully",
        "ward.bed_transfer": "Bed transfer completed",
        "validation.required": "This field is required",
        "validation.invalid_email": "Invalid email address",
        "validation.invalid_phone": "Invalid phone number",
        "validation.min_length": "Must be at least {min} characters",
        "validation.positive_number": "Must be a positive number",
        "system.server_error": "An unexpected error occurred. Please try again.",
        "system.not_found": "The requested resource was not found",
        "system.maintenance": "System is under maintenance. Please try later.",
    },
    "hi": {
        "auth.invalid_credentials": "अमान्य ईमेल या पासवर्ड",
        "auth.token_expired": "सत्र समाप्त हो गया। कृपया फिर से लॉगिन करें।",
        "auth.unauthorized": "आप यह कार्रवाई करने के लिए अधिकृत नहीं हैं",
        "patient.created": "रोगी सफलतापूर्वक पंजीकृत",
        "patient.updated": "रोगी सफलतापूर्वक अपडेट",
        "patient.not_found": "रोगी नहीं मिला",
        "ipd.admission_created": "आईपीडी प्रवेश अनुरोध सफलतापूर्वक बनाया गया",
        "ipd.bed_allocated": "बिस्तर सफलतापूर्वक आवंटित",
        "ipd.billing.payment_processed": "भुगतान सफलतापूर्वक संसाधित",
        "pharmacy.dispensed": "दवा सफलतापूर्वक वितरित",
        "lab.order_placed": "लैब ऑर्डर सफलतापूर्वक दिया गया",
        "validation.required": "यह फ़ील्ड आवश्यक है",
        "system.server_error": "एक अप्रत्याशित त्रुटि हुई। कृपया पुन: प्रयास करें।",
    },
    "ar": {
        "auth.invalid_credentials": "بريد إلكتروني أو كلمة مرور غير صالحة",
        "auth.token_expired": "انتهت الجلسة. الرجاء تسجيل الدخول مرة أخرى.",
        "auth.unauthorized": "غير مصرح لك بتنفيذ هذا الإجراء",
        "patient.created": "تم تسجيل المريض بنجاح",
        "patient.not_found": "المريض غير موجود",
        "ipd.admission_created": "تم إنشاء طلب القبول بنجاح",
        "ipd.bed_allocated": "تم تخصيص السرير بنجاح",
        "validation.required": "هذا الحقل مطلوب",
        "system.server_error": "حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.",
    },
    "es": {
        "auth.invalid_credentials": "Correo electrónico o contraseña inválidos",
        "patient.created": "Paciente registrado exitosamente",
        "patient.not_found": "Paciente no encontrado",
        "validation.required": "Este campo es obligatorio",
        "system.server_error": "Ocurrió un error inesperado. Inténtelo de nuevo.",
    },
    "fr": {
        "auth.invalid_credentials": "E-mail ou mot de passe invalide",
        "patient.created": "Patient enregistré avec succès",
        "patient.not_found": "Patient non trouvé",
        "validation.required": "Ce champ est obligatoire",
        "system.server_error": "Une erreur inattendue s'est produite. Veuillez réessayer.",
    },
    "de": {
        "auth.invalid_credentials": "Ungültige E-Mail oder Passwort",
        "patient.created": "Patient erfolgreich registriert",
        "validation.required": "Dieses Feld ist erforderlich",
        "system.server_error": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
    },
    "zh": {
        "auth.invalid_credentials": "邮箱或密码无效",
        "patient.created": "患者注册成功",
        "validation.required": "此字段为必填项",
        "system.server_error": "发生意外错误，请重试。",
    },
    "ja": {
        "auth.invalid_credentials": "メールアドレスまたはパスワードが無効です",
        "patient.created": "患者の登録が完了しました",
        "validation.required": "この項目は必須です",
        "system.server_error": "予期しないエラーが発生しました。もう一度お試しください。",
    },
    "pt": {
        "auth.invalid_credentials": "E-mail ou senha inválidos",
        "patient.created": "Paciente registrado com sucesso",
        "validation.required": "Este campo é obrigatório",
        "system.server_error": "Ocorreu um erro inesperado. Tente novamente.",
    },
    "ru": {
        "auth.invalid_credentials": "Неверный email или пароль",
        "patient.created": "Пациент успешно зарегистрирован",
        "validation.required": "Это поле обязательно",
        "system.server_error": "Произошла непредвиденная ошибка. Попробуйте снова.",
    },
    "mr": {
        "auth.invalid_credentials": "अवैध ईमेल किंवा पासवर्ड",
        "patient.created": "रुग्ण यशस्वीपणे नोंदणीकृत",
        "validation.required": "हे फील्ड आवश्यक आहे",
        "system.server_error": "अनपेक्षित त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
    },
}


def get_locale_from_header(accept_language: Optional[str] = None) -> str:
    """Extract preferred locale from Accept-Language header."""
    if not accept_language:
        return _fallback_locale
    # Parse "en-US,en;q=0.9,hi;q=0.8" format
    parts = accept_language.replace(" ", "").split(",")
    for part in parts:
        lang = part.split(";")[0].split("-")[0].lower()
        if lang in BACKEND_TRANSLATIONS:
            return lang
    return _fallback_locale


def translate(key: str, locale: str = "en", params: Optional[Dict[str, str]] = None) -> str:
    """Get translated string for a key in the given locale, with fallback to English."""
    translations = BACKEND_TRANSLATIONS.get(locale, {})
    value = translations.get(key) or BACKEND_TRANSLATIONS.get(_fallback_locale, {}).get(key, key)
    
    if params:
        for k, v in params.items():
            value = value.replace(f"{{{k}}}", str(v))
    
    return value


def t(key: str, locale: str = "en", **kwargs) -> str:
    """Shortcut for translate()."""
    return translate(key, locale, kwargs if kwargs else None)


# ─── FastAPI Middleware & Dependencies ────────────────────────────────────
from fastapi import Request

async def get_request_locale(request: Request) -> str:
    """FastAPI dependency to extract locale from request."""
    # Check custom header first (set by frontend)
    locale = request.headers.get("X-Locale")
    if locale and locale in BACKEND_TRANSLATIONS:
        return locale
    # Fallback to Accept-Language
    return get_locale_from_header(request.headers.get("Accept-Language"))
