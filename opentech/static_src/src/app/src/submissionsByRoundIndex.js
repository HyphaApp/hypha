import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { ConnectedRouter } from 'connected-react-router';

import SubmissionsByRoundApp from './SubmissionsByRoundApp';
import createStore, { history } from '@redux/store';


const container = document.getElementById('submissions-by-round-react-app');

const store = createStore();

ReactDOM.render(
    <Provider store={store}>
        <ConnectedRouter history={history}>
            <SubmissionsByRoundApp pageContent={container.innerHTML} roundID={parseInt(container.dataset.roundId)} />
        </ConnectedRouter>
    </Provider>,
    container
);
