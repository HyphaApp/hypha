import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import DisplayPanel from '@components/DisplayPanel';
import { fetchSubmission } from '@actions/submissions';
import {
    getCurrentSubmission,
    getCurrentSubmissionID
} from '@selectors/submissions';

class DisplayPanelContainer extends React.Component {
    componentDidUpdate(prevProps) {
        const { submissionID } = this.props;
        if (submissionID !== undefined && (
             prevProps.submissionID === undefined || submissionID !== prevProps.submissionID
        )) {
            this.props.loadSubmission(submissionID);
        }
    }

    render() {
        const { submission } = this.props;
        return <DisplayPanel submission={submission} />;
    }
}

const mapStateToProps = state => ({
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
});


const mapDispatchToProps = dispatch => ({
    loadSubmission: id => dispatch(fetchSubmission(id)),
});


DisplayPanelContainer.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number,
    loadSubmission: PropTypes.func,
};

export default connect(mapStateToProps, mapDispatchToProps)(DisplayPanelContainer);
