import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import ReviewBlock, { Review, AssignedToReview, Opinion } from '@components/ReviewBlock'

import { getSubmissionOfID } from '@selectors/submissions'


const ReviewInformation = ({ data }) => {
    const staff = [];
    const nonStaff = [];
    Object.values(data.assigned).map(key => key.isStaff ? staff.push(key) : nonStaff.push(key))

    const orderPeople = (people) => {
        people.sort((a,b) => {
            if (a.role.order === null) {
                return 100;
            }
            return a.role.order - b.role.order;
        })

        const hasReviewed = [];
        const notReviewed = [];

        people.map(person => {
            data.reviews.filter(review => person.id === review.authorId)[0] ? hasReviewed.push(person) : notReviewed.push(person);
        });

        return [...hasReviewed, ...notReviewed];
    }

    const renderReviewBlock = (reviewers) => {
        return <ReviewBlock score={data.score} recommendation={data.recommendation.display}>
            {reviewers.map(reviewer => {
                const review = data.reviews.filter(review => review.authorId === reviewer.id)[0];

                if (!review) {
                    return <AssignedToReview key={reviewer.id + '-no-review'} author={reviewer.name} />
                }

                return <Review
                    key={reviewer.id}
                    url={review.reviewUrl}
                    author={reviewer.name}
                    score={review.score}
                    recommendation={review.recommendation} >
                    {review.opinions.map((opinion, i) => {
                        const author = data.assigned.filter(person => person.id === opinion.authorId)[0];
                        return <Opinion
                            key={i}
                            author={author.name}
                            opinion={opinion.opinion}
                        />
                    })}
                </Review>
            })}
        </ReviewBlock>
    }

    const orderedStaff = orderPeople(staff);
    const orderedNonStaff = orderPeople(nonStaff);

    return (
        <>
            <h1>Reviews &amp; assigness</h1>
            {renderReviewBlock(orderedStaff)}
            {renderReviewBlock(orderedNonStaff)}
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
