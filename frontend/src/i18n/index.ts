const langDir = "i18n";
export const locales = [
  {
    name: "English",
    code: "en",
    iso: "en-US",
    file: "en",
    rtl: false,
  },
  {
    name: "فارسی",
    code: "fa",
    iso: "fa-IR",
    file: "fa",
    rtl: true,
  },
];

export async function getMessages() {
  let output: { [key: string]: any } = {};
  try {
    const modules: any = import.meta.glob("@/i18n/*/messages/index.ts");
    for (let locale of locales) {
      output[locale.code] = (
        await modules["/src/i18n/" + locale.file + "/messages/index.ts"]()
      ).default;
    }
  } finally {
    return output;
  }
}
