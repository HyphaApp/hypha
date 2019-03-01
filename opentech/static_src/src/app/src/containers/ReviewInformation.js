import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import ReviewBlock, { Review, AssignedToReview } from '@components/ReviewBlock'

import { getSubmissionOfID } from '@selectors/submissions'


const ReviewInformation = ({ data }) => {
    // const assigned = review.assigned;

    // split in to staff and non-staff
    const staff = [];
    const nonStaff = [];
    Object.values(data.assigned).map(key => key.isStaff ? staff.push(key) : nonStaff.push(key))

    // // order
    // const staffWithRoleAndReview = [];
    // const staffWithReview = [];
    // const staffWithRole = []

    // staff.map(person => {
    //     if (person.role.order && person.review) {
    //         staffWithRoleAndReview.push(person);
    //     } else if (person.review) {
    //         staffWithReview.push(person);
    //     } else if (person.role) {
    //         staffWithRole.push(person)
    //     }
    // });

    const renderReviewBlock = (reviewers) => {
        return <ReviewBlock score={data.score} recommendation={data.recommendation.display}>
            {reviewers.map(reviewer => {
                const review = data.reviews.filter(review => review.authorId === reviewer.id)[0];
                // const opinion = data.reviews.filter(opinion => opinion.opinions.filter(opinion => opinion.authorId === reviewer.id)[0]);

                if (!review) {
                    return <AssignedToReview key={reviewer.id + '-no-review'} author={reviewer.name} />
                }

                return <Review
                    key={reviewer.id}
                    url={review.reviewUrl}
                    author={reviewer.name}
                    score={review.score}
                    recommendation={review.recommendation}
                    opinions={review.opinions}
                />
            })}
        </ReviewBlock>
    }

    // ordered
    // wrap hide/show block around the second reviewblock

    return (
        <>
            <h1>Reviews &amp; assigness</h1>
            {renderReviewBlock(staff)}
            {renderReviewBlock(nonStaff)}
        </>
    )
}

ReviewInformation.propTypes = {
    data: PropTypes.object,
    submissionID: PropTypes.number.isRequired,
}

const mapStateToProps = (state, ownProps) => ({
    data: getSubmissionOfID(ownProps.submissionID)(state).review,
})

export default connect(mapStateToProps)(ReviewInformation)
