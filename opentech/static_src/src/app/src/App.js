import React from 'react';
import ReactDOM from 'react-dom';
import { hot } from 'react-hot-loader'

import './App.scss';

class App extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            detailOpen: false
        }
    }

    detailOpen = (state) => {
        this.setState({style: {display: 'None'}})
        this.setState({detailOpen: true})
    }

    detailClose = () => {
        this.setState({style: {}})
        this.setState({detailOpen: false})
    }

    render () {
        return (
            <div>
                <div>
                    <button className="red-button" onClick={this.detailOpen}>Detail View</button>
                    |
                    <button onClick={this.detailClose}>List View</button>
                </div>
                {this.state.detailOpen && <div><h2>THIS IS REACT</h2></div>}
                <div style={this.state.style} dangerouslySetInnerHTML={ {__html: this.props.originalContent} } />
            </div>
    )}
}

export default hot(module)(App)
