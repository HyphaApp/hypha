import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

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
        const { clearCurrentSubmission, isError, isLoading, submission } = this.props;

        return (
            <Tabber className="display-panel">
                <button onClick={clearCurrentSubmission}>Back</button>
                <Tab name="Application">
                    <ApplicationDisplay isLoading={isLoading} isError={isError} submission={submission} />
                </Tab>
                <Tab name="Notes">
                    <p>Notes</p>
                </Tab>
                <Tab name="Status">
                    <p>Status</p>
                </Tab>
            </Tabber>
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

export default connect(mapStateToProps, mapDispatchToProps)(DisplayPanel);
