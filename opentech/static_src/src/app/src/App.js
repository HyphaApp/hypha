import React from 'react';
import ReactDOM from 'react-dom';
import { hot } from 'react-hot-loader'
import ArrayIcon from './../../images/icon-array.svg';
import GridIcon from './../../images/icon-grid.svg';

import './App.scss';

class App extends React.Component {
    constructor(props) {
        super(props);
        this.originalContent = null;
        this.setOriginalContentRef = element => {
            this.originalContent = element.querySelector('#react-original-content');

            ReactDOM.render(
                <div>
                    <button onClick={this.detailOpen}><ArrayIcon /></button>
                    <button onClick={this.detailClose}><GridIcon /></button>
                </div>,
                element.querySelector('#react-switcher')
            );
        };

        this.state = {
            detailOpen: false
        }
    }

    detailOpen = (state) => {
        this.originalContent.style.display = 'none';
        this.setState({ style: { display: 'None' } })
        this.setState({ detailOpen: true })
    }

    detailClose = () => {
        this.originalContent.style.display = null;
        this.setState({ style: {} })
        this.setState({ detailOpen: false })
    }

    render() {
        return (
            <div>
                <div ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />
                {this.state.detailOpen && <div><h2>THIS IS REACT</h2></div>}
            </div>
        )
    }
}


export default hot(module)(App)
