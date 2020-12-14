import React from 'react';
import ReactDOM from 'react-dom';
import Modal from 'react-modal';
import { Provider } from 'react-redux';
import { ConnectedRouter } from 'connected-react-router';

import AllSubmissionsApp from './AllSubmissionsApp';
import createStore, { history } from '@redux/store';


const container = document.getElementById('submissions-all-react-app');

const store = createStore();

Modal.setAppElement(container)

ReactDOM.render(
    <Provider store={store}>
        <ConnectedRouter history={history}>
            <AllSubmissionsApp pageContent={container.innerHTML}/>
        </ConnectedRouter>
    </Provider>,
    container
);
