import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission, fetchSubmission } from '@actions/submissions';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionErrorState,
    getSubmissionLoadingState,

} from '@selectors/submissions';
import ApplicationDisplay from '@components/ApplicationDisplay'
import Tabber from '@components/Tabber'
import {Tab} from '@components/Tabber'
import './style.scss';


class DisplayPanel extends React.Component  {
    componentDidUpdate(prevProps) {
        const { submissionID } = this.props;
        if (submissionID !== null && (
             prevProps.submissionID === undefined || submissionID !== prevProps.submissionID
        )) {
            this.props.loadSubmission(submissionID);
        }
    }

    render() {
        const { isError, isLoading, submission, windowSize: {windowWidth: width} } = this.props;
        const { clearCurrentSubmission } = this.props;

        const isMobile = width < 1024;

        const application = <ApplicationDisplay isLoading={isLoading} isError={isError} submission={submission} />

        let tabs = [
            <Tab button="Notes" key="note">
                <p>Notes</p>
            </Tab>,
            <Tab button="Status" key="status">
                <p>Status</p>
            </Tab>
        ]

        if ( isMobile ) {
            tabs = [
                <Tab button=<button onClick={clearCurrentSubmission}>Back</button> key="back" />,
                <Tab button="Application" key="application">
                    { application }
                </Tab>,
                ...tabs
            ]
        }

        return (
            <div className="display-panel">
                { !isMobile && (
                    <div className="display-panel__column">
                        <div className="display-panel__header display-panel__header--spacer"></div>
                        <div className="display-panel__body">
                            { application }
                        </div>
                    </div>
                )}
                <div className="display-panel__column">
                    <div className="display-panel__body">
                        <Tabber>
                            { tabs }
                        </Tabber>
                    </div>
                </div>
            </div>

        )
    }
}

const mapStateToProps = state => ({
    isLoading: getSubmissionLoadingState(state),
    isError: getSubmissionErrorState(state),
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
});


const mapDispatchToProps = dispatch => ({
    loadSubmission: id => dispatch(fetchSubmission(id)),
    clearCurrentSubmission: () => dispatch(clearCurrentSubmission()),
});


DisplayPanel.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number,
    loadSubmission: PropTypes.func,
    isLoading: PropTypes.bool,
    isError: PropTypes.bool,
};

export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DisplayPanel));
