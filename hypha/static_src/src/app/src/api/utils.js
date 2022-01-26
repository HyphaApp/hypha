import Cookies from 'js-cookie';

const getBaseUrl = () => {
    return process.env.API_BASE_URL;
};

export function apiFetch({path, method = 'GET', params = new URLSearchParams(), options = {}}) {
    const url = new URL(getBaseUrl());
    url.pathname = url.pathname + path;

    for (const [paramKey, paramValue] of getIteratorForParams(params)) {
        url.searchParams.append(paramKey, paramValue);
    }

    options.headers = options.headers ? options.headers : {};
    options.headers['Accept'] = 'application/json';

    if (['post', 'put', 'patch', 'delete'].includes(method.toLowerCase())) {
        options.headers = {
            ...options.headers,
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        };
    }

    if (path.includes('apply')) {
        url.pathname = path;
        delete options.headers['Content-Type'];
        delete options.headers['Accept'];
        options.headers['Accept'] = '*/*';
        options.headers['X-Requested-With'] = 'XMLHttpRequest';
    }

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers
        },
        method,
        mode: path.includes('apply') ? 'cors' : 'same-origin',
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
