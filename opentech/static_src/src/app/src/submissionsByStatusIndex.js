import React from 'react';
import ReactDOM from 'react-dom';
import Modal from 'react-modal';
import { Provider } from 'react-redux';
import { ConnectedRouter } from 'connected-react-router';

import SubmissionsByStatusApp from './SubmissionsByStatusApp';
import createStore, { history } from '@redux/store';


const container = document.getElementById('submissions-by-status-react-app');

const store = createStore();

Modal.setAppElement(container)

ReactDOM.render(
    <Provider store={store}>
        <ConnectedRouter history={history}>
            <SubmissionsByStatusApp pageContent={container.innerHTML} statuses={container.dataset.statuses.split(',')} />
        </ConnectedRouter>
    </Provider>,
    container
);
