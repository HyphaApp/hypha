import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import ReviewsBlock from '@components/ReviewsBlock'
import { getSubmissionOfID } from '@selectors/submissions'

const ReviewInformation = ({ submission }) => {
    return <ReviewsBlock submission={submission} />
}

ReviewInformation.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number.isRequired,
}

const mapStateToProps = (state, ownProps) => ({
    submission: getSubmissionOfID(ownProps.submissionID)(state),
})

export default connect(mapStateToProps)(ReviewInformation)
