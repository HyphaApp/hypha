import React from 'react';
import ReactDOM from 'react-dom';


const App = <div><h2>THIS IS REACT</h2></div>


const render = Component => {
    ReactDOM.render(
        <Component />,
        document.getElementById('root')
    );
}


render(App)


if (module.hot) {
    module.hot.accept(App, () => {
        const NextApp = App;
        render(NextApp);
    });
}
