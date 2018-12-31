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

    detailOpen = (state) => {this.setState({detailOpen: state})}

    render () {
        return (
            <div>
                <div>
                    <button className="red-button" onClick={() => this.detailOpen(true)}>Detail View</button>
                    |
                    <button onClick={() => this.detailOpen(false)}>List View</button>
                </div>
                {this.state.detailOpen ? (
                    <div><h2>THIS IS REACT</h2></div>
                ) : (
                    <div dangerouslySetInnerHTML={ {__html: this.props.originalContent} } />
                )}
            </div>
    )}
}

export default hot(module)(App)
