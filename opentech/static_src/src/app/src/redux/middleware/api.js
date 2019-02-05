import { camelizeKeys, decamelizeKeys } from 'humps'

import { apiFetch } from '@api/utils'

const callApi = (endpoint) => {
    // If body is an object, decamelize the keys.
    const { options } = endpoint;
    if (options !== undefined && typeof options.body === 'object') {
        endpoint = {
            ...endpoint,
            options: {
                ...options,
                body: JSON.stringify(decamelizeKeys(options.body))
            }
        }
    }

    return apiFetch(endpoint)
        .then(response =>
              response.json().then(json => {
                  if (!response.ok) {
                      return Promise.reject({message: json.error})
                  }
                  return camelizeKeys(json)
              })
             )
}


export const CALL_API = 'Call API'


// A Redux middleware that interprets actions with CALL_API info specified.
// Performs the call and promises when such actions are dispatched.
export default store => next => action => {
    const callAPI = action[CALL_API]

    if (callAPI === undefined) {
        return next(action)
    }

    let { endpoint } = callAPI
    const { types } = callAPI

    if (typeof endpoint === 'function') {
        endpoint = endpoint(store.getState())
    }

    if (typeof endpoint !== 'object' && typeof endpoint.path !== 'string') {
        throw new Error('Specify a string endpoint URL.')
    }

    if (!Array.isArray(types) || types.length !== 3) {
        throw new Error('Expected an array of three action types.')

    }
    if (!types.every(type => typeof type === 'string')) {
        throw new Error('Expected action types to be strings.')
    }

    const actionWith = data => {
        const finalAction = {...action, ...data}
        delete finalAction[CALL_API]
        return finalAction
    }

    const [ requestType, successType, failureType ] = types
    next(actionWith({ type: requestType }))

    return new Promise((resolve, reject) => {
        return callApi(endpoint).then(
            response => {
                resolve();
                return next(actionWith({
                    data: response,
                    type: successType
                }))
            },
            error => {
                reject();
                return next(actionWith({
                    type: failureType,
                    error: error.message || 'Something bad happened'
                }))
            })
    });
}
