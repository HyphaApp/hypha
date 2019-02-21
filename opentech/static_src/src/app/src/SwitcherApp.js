import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import Switcher from '@components/Switcher';
import MessagesContainer from '@containers/MessagesContainer'
import {
    clearCurrentSubmissionParam,
    loadSubmissionFromURL,
    setCurrentSubmissionParam,
} from '@actions/submissions';


class SwitcherApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        detailComponent: PropTypes.node.isRequired,
        switcherSelector: PropTypes.string.isRequired,
        startOpen: PropTypes.bool,
        processParams: PropTypes.func.isRequired,
        searchParam: PropTypes.string,
        setParams: PropTypes.func.isRequired,
        clearParams: PropTypes.func.isRequired,
    };

    state = {
        detailOpened: false,
        mounting: true,
    };

    componentDidMount() {
        this.setState({
            mounting: false
        })

        console.log(this.props.searchParam)
        const success = this.props.processParams(this.props.searchParam)
        if (success) {
            this.openDetail()
        }
    }

    componentDidUpdate(prevProps) {
        if (prevProps.searchParam !== this.props.searchParam) {
            const success = this.props.processParams(this.props.searchParam)

            if (!success) {
                this.closeDetail()
            } else {
                this.openDetail()
            }
        }
    }

    openDetail = () => {
        document.body.classList.add('app-open');
        this.props.setParams();
        this.setState(state => ({
            style: { ...state.style, display: 'none' } ,
            detailOpened: true,
        }));
    }

    closeDetail = () => {
        document.body.classList.remove('app-open');
        this.props.clearParams();
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
                <MessagesContainer />
                <Switcher selector={this.props.switcherSelector} open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpened && this.props.detailComponent}
            </>
        )
    }
}

const mapStateToProps = (state) => ({
    searchParam: state.router.location.search
})

const mapDispatchToProps = dispatch => ({
    processParams: params => dispatch(loadSubmissionFromURL(params)),
    clearParams: () => dispatch(clearCurrentSubmissionParam()),
    setParams: () => dispatch(setCurrentSubmissionParam()),
});

export default connect(mapStateToProps, mapDispatchToProps)(SwitcherApp);
