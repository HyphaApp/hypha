import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import SubmissionDisplay from '@components/SubmissionDisplay';

class CurrentSubmissionDisplay extends React.Component {
    componentDidUpdate(prevProps) {
        const { submissionID } = this.props;
        if (submissionID !== null && (
            prevProps.submissionID === undefined || submissionID !== prevProps.submissionID
        )) {
            this.props.loadSubmission(submissionID);
        }
    }

    render () {
        return <SubmissionDisplay submission={submission} />
    }

}
