import axios from "axios";

export const didAbort = (error: any) => axios.isCancel(error);
export const getCancelSource = () => axios.CancelToken.source();

// Main api function
const api = (axios: any) => {
    // abort function
    const withAbort =
        (fn: any) =>
            async (...args: any) => {
                const originalConfig = args[args.length - 1];
                // Extract abort property from the config
                const { abort, ...config } = originalConfig;
                // Create cancel token and abort method only if abort
                // function was passed
                if (typeof abort === "function") {
                    const { cancel, token } = getCancelSource();
                    config.cancelToken = token;
                    abort(cancel);
                }
                try {
                    // Spread all arguments from args besides the original config,
                    // and pass the rest of the config without abort property
                    return await fn(...args.slice(0, args.length - 1), config);
                } catch (error: any) {
                    // Add "aborted" property to the error if the request was cancelled
                    didAbort(error) && (error.aborted = true);
                    throw error;
                }
            };

    const withLogger = async (promise: any) =>
        promise.catch((error: any) => {
            // eslint-disable-next-line no-undef
            /*
                  Always log errors in dev environment
                  if (process.env.NODE_ENV !== 'development') throw error
                  */
            // Log error only if DEV env is set to true
            if (!import.meta.env.DEV) throw error;
            if (error.response) {
                // The request was made and the server responded with a status code
                // that falls out of the range of 2xx
                console.log("Error Response Data: ", error.response.data);
                console.log("Error Response Status: ", error.response.status);
                console.log("Error Response Headers: ", error.response.headers);
            } else if (error.request) {
                // The request was made but no response was received
                // `error.request` is an instance of XMLHttpRequest
                // in the browser and an instance of
                // http.ClientRequest in node.js
                console.log("Request Error", error.request);
            } else {
                // Something happened in setting up the request that triggered an Error
                console.log("Error", error.message);
            }
            console.log("Error Config: ", error.config);

            throw error;
        });

    // Wrapper functions around axios
    return {
        get: (url: string, config = {}) =>
            withLogger(withAbort(axios.get)(url, config)),
        post: (url: string, body: object, config = {}) =>
            withLogger(withAbort(axios.post)(url, body, config)),
        put: (url: string, body: object, config = {}) =>
            withLogger(withAbort(axios.put)(url, body, config)),
        patch: (url: string, body: object, config = {}) =>
            withLogger(withAbort(axios.patch)(url, body, config)),
        delete: (url: string, config = {}) =>
            withLogger(withAbort(axios.delete)(url, config)),
        defaults: axios.defaults,
    };
};
// Initialise the api function and pass axiosInstance to it
export default api;
