import React from 'react';
import ReactDOM from 'react-dom';

import App from './App'


const container = document.getElementById('react-app')


ReactDOM.render(
    <App originalContent={container.innerHTML} />,
    container
);
