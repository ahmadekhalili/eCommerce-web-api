import { app } from "./app";
import "@/plugins/vuetify.ts";
import "@/plugins/pinia";
import "@/plugins/router";
import "@/plugins/i18n";

// fonts
import "@/assets/fonts/IRANSans.scss";
import "@/assets/fonts/IRANSans_FaNum.scss";

// styles
import "@/globalStyles/globalStyle.scss";
import "vue3-carousel/dist/carousel.css";

app.mount("#app");
