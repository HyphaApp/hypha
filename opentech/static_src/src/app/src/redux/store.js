import { createStore, applyMiddleware } from 'redux'
import ReduxThunk from 'redux-thunk'
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly'
import logger from 'redux-logger'

import rootReducer from '@reducers';


export default initialState => {
    const store = createStore(
        rootReducer,
        composeWithDevTools(
            applyMiddleware(
                ReduxThunk,
                logger,
            )
        )
    )
    return store;
};
