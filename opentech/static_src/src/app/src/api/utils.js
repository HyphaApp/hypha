import { decamelizeKeys } from 'humps';
import Cookies from 'js-cookie';

const getBaseUrl = () => {
    return process.env.API_BASE_URL;
};

export function apiFetch({path, method = 'GET', params = {}, options = {}, decamelizeJSON = true}) {
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

    if (decamelizeJSON === true && options.body !== undefined) {
        options = {
            ...options,
            body: JSON.stringify(decamelizeKeys(options.body))
        }
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
