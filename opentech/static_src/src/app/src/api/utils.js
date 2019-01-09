const getBaseUrl = () => {
    return 'http://apply.localhost:8000/';
};

export async function apiFetch(path, method = 'GET', params, options) {
    console.log('apifetch');
    const url = new URL(getBaseUrl());
    url.pathname = path;

    if (params !== undefined) {
        url.searchParams = new URLSearchParams(params);
    }

    return fetch(url, {
        ...options,
        method,
        mode: 'same-origin',
    });
}
