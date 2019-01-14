const getBaseUrl = () => {
    return 'http://apply.localhost:8000/';
};

export async function apiFetch(path, method = 'GET', params, options) {
    const url = new URL(getBaseUrl());
    url.pathname = path;

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
