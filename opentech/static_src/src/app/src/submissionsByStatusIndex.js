import React from 'react';
import ReactDOM from 'react-dom';
import Modal from 'react-modal';
import { Provider } from 'react-redux';

import SubmissionsByStatusApp from './SubmissionsByStatusApp';
import createStore from '@redux/store';


const container = document.getElementById('submissions-by-status-react-app');

const store = createStore();

Modal.setAppElement(container)

ReactDOM.render(
    <Provider store={store}>
        <SubmissionsByStatusApp pageContent={container.innerHTML} statuses={container.dataset.statuses.split(',')} />
    </Provider>,
    container
);
