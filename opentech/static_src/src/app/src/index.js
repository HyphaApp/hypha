import React from 'react';
import ReactDOM from 'react-dom';

import SubmissionsByRoundApp from './SubmissionsByRoundApp'


const container = document.getElementById('submissions-by-round-react-app');


ReactDOM.render(
    <SubmissionsByRoundApp pageContent={container.innerHTML} />,
    container
);
