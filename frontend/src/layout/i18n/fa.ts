import type { default as i18n, footer as footerType } from "./../models/i18n";

const footer = (): footerType => {
  return {
    "about-us": "درباره ما",
    "about-us-description":
      "گروه SMELLSHOP  آماده ارائه خدمات مشاوره و فروش در حوزه عطر و ادکلن می باشد.",
    "contact-us": "تماس با ما",
    "new-fragrances": "عطرهای جدید",
    "privacy-policy": "سیاست حفظ حریم خصوصی",
    "product-specifications": "مشخصات محصول",
    "return-policy": "سیاست بازگشت",
    "terms-and-conditions": "شرایط و ضوابط",
    "useful-links": "لینک های مفید",
    newsletter: "خبرنامه",
    subscribe: "اشتراک",
    "subscribe-description":
      "برای دریافت به‌روزرسانی‌ها، دسترسی به معاملات انحصاری و موارد دیگر مشترک شوید.",
    "enter-your-email-address": "آدرس ایمیل خود را وارد کنید0",
  };
};
const i18n = (): i18n => {
  return {
    footer: footer(),
  };
};
