import { createStore, applyMiddleware } from 'redux'
import ReduxThunk from 'redux-thunk'
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly'
import logger from 'redux-logger'

import rootReducer from '@reducers';

const MIDDLEWARE = [
    ReduxThunk,
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
