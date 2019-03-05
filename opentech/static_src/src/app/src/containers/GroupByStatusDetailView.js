import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import DetailView from '@components/DetailView'
import ByStatusListing from '@containers/ByStatusListing'
import {
    getSubmissionsByRoundError,
    getCurrentRoundSubmissions,
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionErrorState,
} from '@selectors/submissions';
import {
    getCurrentRound,
} from '@selectors/rounds';


const GroupByStatusDetailView = ({ currentSubmission, round, isErrored, submissions, submissionID, errorMessage }) => {
    const listing = <ByStatusListing />
    const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
    const isEmpty = submissions.length === 0
    const activeSubmision = !!submissionID

    return (
        <DetailView
            isErrored={isErrored}
            listing={listing}
            isEmpty={isEmpty}
            isLoading={isLoading}
            showSubmision={activeSubmision}
            errorMessage={errorMessage || 'Fetching failed.'}
        />
    );
}

GroupByStatusDetailView.propTypes = {
    submissions: PropTypes.arrayOf(PropTypes.object),
    submissionID: PropTypes.number,
    round: PropTypes.object,
    isErrored: PropTypes.bool,
    errorMessage: PropTypes.string,
    currentSubmission: PropTypes.shape({
        status: PropTypes.string
    }),
}

const mapStateToProps = state => ({
    round: getCurrentRound(state),
    isErrored: getSubmissionErrorState(state),
    errorMessage: getSubmissionsByRoundError(state),
    submissions: getCurrentRoundSubmissions(state),
    currentSubmission: getCurrentSubmission(state),
    submissionID: getCurrentSubmissionID(state),
})


export default connect(mapStateToProps)(
    GroupByStatusDetailView
)
