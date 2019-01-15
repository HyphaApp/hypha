const getBaseUrl = () => {
    return process.env.API_BASE_URL;
};

export async function apiFetch(path, method = 'GET', params, options) {
    console.log('getBaseUrl', getBaseUrl());
    const url = new URL(getBaseUrl());
    console.log(url);
    url.pathname = path;
    console.log(url);

    if (params !== undefined) {
        for (const [paramKey, paramValue] of Object.entries(params)) {
            url.searchParams.set(paramKey, paramValue);
        }
    }
    return fetch(url, {
        ...options,
        method,
        mode: 'same-origin',
    });
}
