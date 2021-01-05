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
import GeneralInfoContainer from '@containers/GeneralInfo'
import SubmissionFiltersContainer from '@containers/SubmissionFilters'


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
        onFilter: PropTypes.func,
        doNotRenderFilter: PropTypes.array
    };

    state = {
        detailOpened: false,
        mounting: true,
    };

    componentDidMount() {
        this.setState({
            mounting: false
        })

        const success = this.props.processParams(this.props.searchParam)
        if (success) {
            this.openDetail()
        }

        const script = document.createElement("script");
        script.src = "/static/tinymce/js/tinymce/tinymce.min.js";
        script.async = true;
        document.body.appendChild(script);
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
                <GeneralInfoContainer />
                <MessagesContainer />
                <Switcher selector={this.props.switcherSelector} open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />
                {this.state.detailOpened && <SubmissionFiltersContainer onFilter={this.props.onFilter} doNotRender={this.props.doNotRenderFilter}/>}
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
