import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import { MESSAGE_TYPES, addMessage } from '@actions/messages'
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


const GroupByStatusDetailView = ({ addMessage, currentSubmission, round, isErrored, submissions, submissionID, errorMessage }) => {
    const listing = <ByStatusListing />
    const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
    const isEmpty = submissions.length === 0
    const activeSubmision = !!submissionID
    const [ currentStatus, setCurrentStatus ] = useState(undefined)
    const [ localSubmissionID, setLocalSubmissionID ] = useState(submissionID)

    useEffect(() => {
        setCurrentStatus(undefined)
        setLocalSubmissionID(submissionID)
    }, [submissionID])

    useEffect(() => {
        if (localSubmissionID !== submissionID) {
            return;
        }

        if (!currentSubmission || !currentSubmission.status) {
            setCurrentStatus(undefined)
            return;
        }

        const { status, changedLocally } = currentSubmission

        if (currentStatus && status !== currentStatus && !changedLocally) {
            addMessage(
                'The status of this application has changed by another user.',
                MESSAGE_TYPES.INFO
            )
        }

        setCurrentStatus(status)
    })

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
    addMessage: PropTypes.func,
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


const mapDispatchToProps = dispatch => ({
    addMessage: (message, type) => dispatch(addMessage(message, type)),
})

export default connect(mapStateToProps, mapDispatchToProps)(
    GroupByStatusDetailView
)
