import { app } from "@/app";
import { createI18n } from "vue-i18n";
import { getMessages } from "@/i18n/index";

const messages: any = await getMessages();

export const i18n = await createI18n({
  locale: "en",
  fallbackLocale: "en",
  messages,
});
app.use(i18n);
