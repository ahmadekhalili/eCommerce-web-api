import { app } from "@/app";
// Styles
import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";
// Vuetify
import router from "@/router";
import { createVuetify } from "vuetify";
import type { ThemeDefinition } from "vuetify";
const light: ThemeDefinition = {
  dark: true,
  colors: {
    background: "#ffffff",
    surface: "#efefef",
    primary: "#F05D8C",
    "text-primary": "#000000",
    secondary: "#C09F80",
    error: "#B00020",
    info: "#2196F3",
    success: "#4CAF50",
    warning: "#FB8C00",
  },
  variables: {
    alpha1: "44",
    alpha2: "88",
    alpha3: "bb",
  },
};

app.use(
  createVuetify({
    theme: {
      defaultTheme: "light",
      themes: {
        light,
      },
    },
  })
);
