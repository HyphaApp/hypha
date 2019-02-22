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
    getCurrentStatusesSubmissions,
    getCurrentSubmissionID,
} from '@selectors/submissions';
import {
    getByStatusesLoading,
    getByStatusesError,
} from '@selectors/statuses';


class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissions: PropTypes.arrayOf(PropTypes.object),
        submissionID: PropTypes.number,
        isLoading: PropTypes.bool,
        isErrored: PropTypes.bool,
        errorMessage: PropTypes.string,
    };

    render() {
        const { isLoading, isErrored, submissions, submissionID, errorMessage } = this.props;
        const isEmpty = submissions.length === 0;
        const activeSubmision = !!submissionID;

        return (
            <DetailView
                isEmpty={isEmpty}
                listing={<ByRoundListing />}
                isLoading={isLoading}
                showSubmision={activeSubmision}
                isErrored={isErrored}
                errorMessage={errorMessage || "Something went wrong"}
            />
        );
    }
}

const mapStateToProps = (state, ownProps) => ({
    isErrored: getRoundsErrored(state) || getByStatusesError(state),
    isLoading: (
        getByStatusesLoading(state) || getRoundsFetching(state)
    ),
    submissions: getCurrentStatusesSubmissions(state),
    submissionID: getCurrentSubmissionID(state),
})

export default connect(
    mapStateToProps,
)(GroupByRoundDetailView);
