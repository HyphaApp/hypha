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

    state = {
        listingShown: true,
        firstRender: true,
    }

    isMobile = (width) => (width ? width : this.props.windowSize.windowWidth) < 1024

    renderDisplay () {
        return <DisplayPanel />
    }

    componentDidUpdate (prevProps, prevState) {
        if (this.isMobile()) {
            const haveCleared = prevProps.submissionID && !this.props.submissionID
            const haveUpdated = !prevProps.submissionID && this.props.submissionID

            if ( haveCleared ) {
                this.setState({listingShown: true})
            } else if ( haveUpdated && this.state.firstRender ) {
                // Listing automatically updating after update
                // clear, but dont run again
                this.props.clearSubmission()
                this.setState({firstRender: false})
            } else if ( prevProps.submissionID !== this.props.submissionID) {
                // Submission has changed and we want to show it
                // reset the firstRender so that we can clear it again
                this.setState({
                    listingShown: false,
                    firstRender: true,
                })
            }
        }
    }

    render() {
        const { listing } = this.props;

        if (this.isMobile()) {
            var activeDisplay;
            if (this.state.listingShown){
                activeDisplay = (
                    <SlideOutLeft key={"listing"}>
                        {listing}
                    </SlideOutLeft>
                )
            } else {
                activeDisplay = (
                    <SlideInRight key={"display"}>
                        { this.renderDisplay() }
                    </SlideInRight>
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
