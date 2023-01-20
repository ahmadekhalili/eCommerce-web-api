import api from "../../api";
// base URL for profiling application
api.defaults.baseURL = import.meta.env.DEV
    ? "url3"
    : "url4";

export default api;
