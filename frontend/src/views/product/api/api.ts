import axios from "axios";
import api from "@/api/api";

// Create axios instance with default params
const axiosInstance = axios.create();
const productAxios = api(axiosInstance);

productAxios.defaults.baseURL = import.meta.env.DEV
  ? window.location.origin + "/proxy/"
  : "localhost";
productAxios.defaults.withCredentials = true;

export default productAxios;
