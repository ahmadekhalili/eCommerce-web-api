import { getI18NViewsVariables } from "../services";
import messages from "./messages";
// get apps variables
const modules: any = import.meta.glob("@/views/*/i18n/fa.ts");
const appsVariables = await getI18NViewsVariables(modules);
console.log(appsVariables);

export default {
  apps: appsVariables,
  messages,
};
