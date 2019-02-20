import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import ReviewBlock from '@components/ReviewBlock'
import { getSubmissionOfID } from '@selectors/submissions'

const ReviewInformation = ({ review }) => {
    return <ReviewBlock review={review} />
}

ReviewInformation.propTypes = {
    review: PropTypes.object,
    submissionID: PropTypes.number.isRequired,
}

const mapStateToProps = (state, ownProps) => ({
    review: getSubmissionOfID(ownProps.submissionID)(state).review,
})

export default connect(mapStateToProps)(ReviewInformation)
