import React from 'react';
import ReactDOM from 'react-dom';
import Modal from 'react-modal';
import { Provider } from 'react-redux';
import GroupedApplications from '@containers/GroupedApplications';
import createStore, { history } from '@redux/store';
import { ConnectedRouter } from 'connected-react-router';


const container = document.getElementById('grouped-applications-list');

const store = createStore();

Modal.setAppElement(container)

ReactDOM.render(
    <Provider store={store}>
        <ConnectedRouter history={history}>
            <GroupedApplications />
        </ConnectedRouter>
    </Provider>,
    container
);
