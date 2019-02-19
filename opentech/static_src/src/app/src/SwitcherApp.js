import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import Switcher from '@components/Switcher';
import { loadSubmissionFromURL } from '@actions/submissions';

class SwitcherApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        detailComponent: PropTypes.node.isRequired,
        switcherSelector: PropTypes.string.isRequired,
        startOpen: PropTypes.bool,
        processParams: PropTypes.func.isRequired,
    };

    state = {
        detailOpened: false,
        mounting: true,
    };

    componentDidMount() {
        this.setState({
            mounting: false
        })

        const success = this.props.processParams()
        if (success) {
            this.openDetail()
        }

    }

    openDetail = () => {
        document.body.classList.add('app-open');
        this.setState(state => ({
            style: { ...state.style, display: 'none' } ,
            detailOpened: true,
        }));
    }

    closeDetail = () => {
        document.body.classList.remove('app-open');
        this.setState(state => {
            const newStyle = { ...state.style };
            delete newStyle.display;
            return {
                style: newStyle,
                detailOpened: false,
            };
        });
    }

    render() {
        if ( this.state.mounting ) {
            return null
        }
        return (
            <>
                <Switcher selector={this.props.switcherSelector} open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpened && this.props.detailComponent}
            </>
        )
    }
}

const mapDispatchToProps = dispatch => ({
    processParams: id => dispatch(loadSubmissionFromURL()),
});

export default connect(null, mapDispatchToProps)(SwitcherApp);
