import React, { Component } from 'react'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission } from '@actions/submissions';
import DisplayPanel from '@containers/DisplayPanel';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'

import LoadingPanel from '@components/LoadingPanel';

import './style.scss';

class DetailView extends Component {
    static propTypes = {
        listing: PropTypes.element.isRequired,
        showSubmision: PropTypes.bool,
        windowSize: PropTypes.objectOf(PropTypes.number),
        clearSubmission: PropTypes.func.isRequired,
        isLoading: PropTypes.bool,
        errorMessage: PropTypes.string,
        isEmpty: PropTypes.bool,
        isErrored: PropTypes.bool,
    };

    isMobile = (width) => (width ? width : this.props.windowSize.windowWidth) < 1024

    renderDisplay () {
        return <DisplayPanel />
    }

    render() {
        const { listing, isLoading, isErrored, isEmpty, showSubmision, errorMessage } = this.props;

        if (!this.props.windowSize.windowWidth) {
            return null
        }

        if (this.isMobile()) {
            var activeDisplay;
            if (showSubmision) {
                activeDisplay = (
                    <SlideInRight key={"display"}>
                        { this.renderDisplay() }
                    </SlideInRight>
                )
            } else {
                activeDisplay = (
                    <SlideOutLeft key={"listing"}>
                        { React.cloneElement(listing, { shouldSelectFirst: false }) }
                    </SlideOutLeft>
                )
            }

            return (
                <div className="detail-view">
                    { activeDisplay }
                </div>
            )
        } else {
            if (isLoading) {
                return (
                    <LoadingPanel />
                )
            } else if (isErrored) {
                return (
                    <div className="loading-panel">
                        <h5>Something went wrong!</h5>
                        <p>{errorMessage}</p>
                    </div>
                )
            } else if (!isLoading && isEmpty) {
                return (
                    <div className="loading-panel">
                        <h5>No submissions available</h5>
                    </div>
                )
            }
            return (
                <div className="detail-view">
                    {listing}
                    { this.renderDisplay() }
                </div>
            )
        }
    }
}

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission
}

export default connect(null, mapDispatchToProps)(withWindowSizeListener(DetailView));
