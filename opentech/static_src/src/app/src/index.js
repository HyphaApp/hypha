import React from 'react';
import ReactDOM from 'react-dom';

import App from './App'


const container = document.getElementById('react-app');


ReactDOM.render(
    <App pageContent={container.innerHTML} originalContent={document.getElementById('react-original-content')} />,
    container
);
