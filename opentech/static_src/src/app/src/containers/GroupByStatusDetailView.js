import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';

import {
    getCurrentRound,
    getSubmissionsByRoundError,
    getCurrentRoundSubmissions,
    getCurrentSubmissionID,
} from '@selectors/submissions';


class GroupByStatusDetailView extends React.Component {
    static propTypes = {
        submissions: PropTypes.arrayOf(PropTypes.object),
        submissionID: PropTypes.number,
        round: PropTypes.object,
        error: PropTypes.string,
    };

    render() {
        const listing = <ByStatusListing />;
        const { round, error, submissions, submissionID } = this.props;
        const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
        const isEmpty = submissions.length === 0;
        const activeSubmision = !!submissionID;

        return (
            <DetailView
                error={error}
                listing={listing}
                isEmpty={isEmpty}
                isLoading={isLoading}
                showSubmision={activeSubmision}
            />
        );
    }
}

const mapStateToProps = state => ({
    round: getCurrentRound(state),
    error: getSubmissionsByRoundError(state),
    submissions: getCurrentRoundSubmissions(state),
    submissionID: getCurrentSubmissionID(state),
})

export default connect(
    mapStateToProps,
)(GroupByStatusDetailView);
