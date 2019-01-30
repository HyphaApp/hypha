import Cookies from 'js-cookie';

const getBaseUrl = () => {
    return process.env.API_BASE_URL;
};

export async function apiFetch({path, method = 'GET', params = {}, options = {}}) {
    const url = new URL(getBaseUrl());
    url.pathname = path;

    if (params !== undefined) {
        for (const [paramKey, paramValue] of Object.entries(params)) {
            url.searchParams.set(paramKey, paramValue);
        }
    }

    if (['post', 'put', 'patch', 'delete'].includes(method.toLowerCase())) {
        options.headers = {
            ...options.headers,
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        };
    }

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Accept': 'application/json',
        },
        method,
        mode: 'same-origin',
        credentials: 'include'
    });
}

function getCSRFToken() {
    return Cookies.get('csrftoken');
}
