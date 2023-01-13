import { app } from "@/app";
import { createPinia } from "pinia";

const pinia = createPinia();
app.use(pinia);
