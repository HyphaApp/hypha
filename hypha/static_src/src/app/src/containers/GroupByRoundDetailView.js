import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import DetailView from '@components/DetailView'
import ByRoundListing from '@containers/ByRoundListing'
import {
    getRoundsFetching,
    getRoundsErrored,
} from '@selectors/rounds'
import {
    getCurrentSubmissionID,
} from '@selectors/submissions';
import {
    getByStatusesLoading,
    getByStatusesError,
} from '@selectors/statuses';

const GroupByRoundDetailView = props => {
    const listing = <ByRoundListing submissionStatuses={props.submissionStatuses} groupBy = {props.groupBy && props.groupBy}/>
    const { isLoading, isErrored, submissions, submissionID, errorMessage } = props
    const isEmpty = submissions.length === 0
    const activeSubmission = !!submissionID
    return (
        <DetailView
            isEmpty={isEmpty}
            listing={listing}
            isLoading={isLoading}
            showSubmision={activeSubmission}
            isErrored={isErrored}
            errorMessage={errorMessage}
        />
    )
}

GroupByRoundDetailView.propTypes = {
    submissionStatuses: PropTypes.arrayOf(PropTypes.string),
    submissions: PropTypes.arrayOf(PropTypes.object),
    submissionID: PropTypes.number,
    isLoading: PropTypes.bool,
    isErrored: PropTypes.bool,
    errorMessage: PropTypes.string,
    groupBy: PropTypes.string
}

const mapStateToProps = (state, ownProps) => ({
    isErrored: getRoundsErrored(state) || getByStatusesError(state),
    isLoading: (
        getByStatusesLoading(state) || getRoundsFetching(state)
    ),
    submissionID: getCurrentSubmissionID(state),
})


export default connect(mapStateToProps)(GroupByRoundDetailView)
