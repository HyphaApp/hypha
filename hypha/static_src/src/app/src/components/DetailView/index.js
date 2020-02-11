import React from 'react'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission } from '@actions/submissions';
import DisplayPanel from '@containers/DisplayPanel';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'

import FullScreenLoadingPanel from '@components/FullScreenLoadingPanel';

import './style.scss';

const DetailView = props => {
    const isMobile = (width) => (width ? width : props.windowSize.windowWidth) < 1024

    const renderDisplay = () => <DisplayPanel />

    const { listing, isLoading, isErrored, isEmpty, showSubmision, errorMessage } = props

    if (isErrored) {
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

    if (!props.windowSize.windowWidth) {
        return null
    }

    let activeDisplay

    if (isMobile()) {
        if (showSubmision) {
            activeDisplay = (
                <SlideInRight key={"display"}>
                    { renderDisplay() }
                </SlideInRight>
            )
        } else {
            activeDisplay = (
                <SlideOutLeft key={"listing"}>
                    { React.cloneElement(listing, { shouldSelectFirst: false }) }
                </SlideOutLeft>
            )
        }
    } else {
        activeDisplay = (
            <>
                {listing}
                {renderDisplay()}
            </>
        )
    }
    return (
        <>
            {isLoading &&
                <FullScreenLoadingPanel />
            }
            <div className="detail-view">
                {activeDisplay}
            </div>
        </>
    )
}

DetailView.propTypes = {
    listing: PropTypes.element.isRequired,
    showSubmision: PropTypes.bool,
    windowSize: PropTypes.objectOf(PropTypes.number),
    clearSubmission: PropTypes.func.isRequired,
    isLoading: PropTypes.bool,
    errorMessage: PropTypes.string,
    isEmpty: PropTypes.bool,
    isErrored: PropTypes.bool,
}

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission
}

export default connect(null, mapDispatchToProps)(withWindowSizeListener(DetailView));
