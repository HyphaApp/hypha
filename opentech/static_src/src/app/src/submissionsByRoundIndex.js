import React from 'react';
import ReactDOM from 'react-dom';
import Modal from 'react-modal';
import { Provider } from 'react-redux';

import SubmissionsByRoundApp from './SubmissionsByRoundApp';
import createStore from '@redux/store';


const container = document.getElementById('submissions-by-round-react-app');

const store = createStore();

Modal.setAppElement(container)

ReactDOM.render(
    <Provider store={store}>
        <SubmissionsByRoundApp pageContent={container.innerHTML} roundID={parseInt(container.dataset.roundId)} />
    </Provider>,
    container
);
