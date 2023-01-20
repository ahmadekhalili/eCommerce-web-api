import type { default as i18n, footer as footerType } from "./../models/i18n";

const footer = (): footerType => {
  return {
    "about-us": "About Us",
    "about-us-description":
      "SMELLSHOP group is ready to provide consulting and sales services in the field of perfume and cologne.",
    "contact-us": "Contact Us",
    "new-fragrances": "New Fragrances",
    "privacy-policy": "Privacy Policy",
    "product-specifications": "Product Specifications",
    "return-policy": "Return Policy",
    "terms-and-conditions": "Terms and Conditions",
    "useful-links": "Useful Links",
    newsletter: "Newsletter",
    subscribe: "Subscribe",
    "subscribe-description":
      "Subscribe to receive updates, access to exclusive deals, and more.",
    "enter-your-email-address": "Enter your email address",
  };
};
const i18n = (): i18n => {
  return {
    footer: footer(),
  };
};
