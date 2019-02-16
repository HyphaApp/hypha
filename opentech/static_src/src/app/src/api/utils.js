import Cookies from 'js-cookie';

const getBaseUrl = () => {
    return process.env.API_BASE_URL;
};

export function apiFetch({path, method = 'GET', params = new URLSearchParams, options = {}}) {
    const url = new URL(getBaseUrl());
    url.pathname = path;

    for (const [paramKey, paramValue] of getIteratorForParams(params)) {
        url.searchParams.append(paramKey, paramValue);
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


function getIteratorForParams(params) {
    if (params instanceof URLSearchParams) {
        return params;
    }

    return Object.entries(params);
}
