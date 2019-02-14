import { createStore, applyMiddleware } from 'redux'
import ReduxThunk from 'redux-thunk'
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly'
import logger from 'redux-logger'
import { routerMiddleware } from 'connected-react-router';
import { createBrowserHistory } from 'history';

import rootReducer from '@reducers';
import api from '@middleware/api'

export const history = createBrowserHistory()

const MIDDLEWARE = [
    routerMiddleware(history),
    ReduxThunk,
    api,
];

if (process.env.NODE_ENV === 'development') {
    MIDDLEWARE.push(logger);
}


export default initialState => {
    const store = createStore(
        rootReducer,
        composeWithDevTools(
            applyMiddleware(...MIDDLEWARE)
        )
    )
    return store;
};
