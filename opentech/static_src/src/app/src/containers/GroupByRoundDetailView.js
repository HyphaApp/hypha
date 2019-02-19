import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByRoundListing from '@containers/ByRoundListing';
import {
    getRoundsFetching,
    getRoundsErrored,
} from '@selectors/rounds';
import {
    getByGivenStatusesLoading,
    getByGivenStatusesError,
    getCurrentRoundSubmissions,
    getCurrentSubmissionID,
} from '@selectors/submissions';

class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
        submissions: PropTypes.arrayOf(PropTypes.object),
        submissionID: PropTypes.number,
        isLoading: PropTypes.bool,
        isErrored: PropTypes.bool,
        errorMessage: PropTypes.string,
    };

    render() {
        const listing = <ByRoundListing submissionStatuses={this.props.submissionStatuses} />;
        const { isLoading, isErrored, submissions, submissionID, errorMessage } = this.props;
        const isEmpty = submissions.length === 0;
        const activeSubmision = !!submissionID;

        return (
            <DetailView
                isEmpty={isEmpty}
                listing={listing}
                isLoading={isLoading}
                showSubmision={activeSubmision}
                isErrored={isErrored}
                errorMessage={errorMessage || 'Fetching failed.'}
            />
        );
    }
}

const mapStateToProps = (state, ownProps) => ({
    isErrored: getRoundsErrored(state),
    errorMessage: getByGivenStatusesError(ownProps.submissionStatuses)(state),
    isLoading: (
        getByGivenStatusesLoading(ownProps.submissionStatuses)(state) ||
        getRoundsFetching(state)
    ),
    submissions: getCurrentRoundSubmissions(state),
    submissionID: getCurrentSubmissionID(state),
})

export default connect(
    mapStateToProps,
)(GroupByRoundDetailView);
