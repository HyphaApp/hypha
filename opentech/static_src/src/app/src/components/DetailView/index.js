import React, { Component } from 'react'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission } from '@actions/submissions';
import DisplayPanel from '@containers/DisplayPanel';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'
import { getCurrentSubmissionID } from '@selectors/submissions';

import './style.scss';

class DetailView extends Component {
    static propTypes = {
        listing: PropTypes.element.isRequired,
        submissionID: PropTypes.number,
        windowSize: PropTypes.objectOf(PropTypes.number),
        clearSubmission: PropTypes.func.isRequired,
    };

    isMobile = (width) => (width ? width : this.props.windowSize.windowWidth) < 1024

    renderDisplay () {
        return <DisplayPanel />
    }

    render() {
        const { listing, submissionID } = this.props;

        const activeSubmision = !!submissionID;

        if (this.isMobile()) {
            var activeDisplay;
            if (activeSubmision) {
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
            return (
                <div className="detail-view">
                    {listing}
                    { this.renderDisplay() }
                </div>
            )
        }

    }
}

const mapStateToProps = state => ({
    submissionID: getCurrentSubmissionID(state),
});

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission
}


export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DetailView));
