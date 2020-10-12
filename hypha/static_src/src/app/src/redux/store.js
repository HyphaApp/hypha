import { createStore, applyMiddleware } from 'redux'
import ReduxThunk from 'redux-thunk'
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly'
import logger from 'redux-logger'
import { routerMiddleware } from 'connected-react-router';
import { createBrowserHistory } from 'history';
import createSagaMiddleware from 'redux-saga';
import createRootReducer from '@reducers';
import api from '@middleware/api'

const sagaMiddleware = createSagaMiddleware();
export const history = createBrowserHistory();

const MIDDLEWARE = [
    routerMiddleware(history),
    ReduxThunk,
    api,
    sagaMiddleware
];

if (process.env.NODE_ENV === 'development') {
    MIDDLEWARE.push(logger);
}


export default initialState => {
    const store = createStore(
        createRootReducer(),
        initialState,
        composeWithDevTools(
            applyMiddleware(...MIDDLEWARE)
        )
    )


  store.runSaga = sagaMiddleware.run;
  store.injectedReducers = {}; // Reducer registry
  store.injectedSagas = {}; // Saga registry
    return store;
};
