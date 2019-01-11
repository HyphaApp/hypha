import React from 'react';
import { hot } from 'react-hot-loader'
import Switcher from './components/Switcher'
import './App.scss';


class App extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            detailOpen: false
        }
    }

    detailOpen = (state) => {
        this.setState({ style: { display: 'none' } })
        this.setState({ detailOpen: true })
    }

    detailClose = () => {
        this.setState({ style: {} })
        this.setState({ detailOpen: false })
    }

    render() {
        return (
            <>
                <Switcher selector='react-switcher' open={this.state.detailOpen} handleOpen={this.detailOpen} handleClose={this.detailClose} />
                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />
                {this.state.detailOpen && <div><h2>THIS IS REACT</h2></div>}
            </>
        )
    }
}


export default hot(module)(App)
