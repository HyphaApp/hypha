import React from 'react';
import ReactDOM from 'react-dom';

import App from './App'

const render = Component => {
    ReactDOM.render(
        <Component />,
        document.getElementById('react-app')
    );
}


render(App)


if (module.hot) {
    module.hot.accept('./App', () => {
        const NextApp = require('./App').default;
        render(NextApp);
    });
}
