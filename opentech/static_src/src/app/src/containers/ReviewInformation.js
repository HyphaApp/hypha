import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import LoadingPanel from '@components/LoadingPanel'
import ReviewBlock, { Review, AssignedToReview, Opinion } from '@components/ReviewBlock'

import { getSubmissionOfID } from '@selectors/submissions'


const ReviewInformation = ({ data }) => {
    if (data === undefined) {
        return <LoadingPanel />
    }

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
        return <>
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
        </>
    }

    const orderedStaff = orderPeople(staff);
    const orderedNonStaff = orderPeople(nonStaff);

    return (
        <div className="review-block">
            <h5>Reviews &amp; assigness</h5>
            <ReviewBlock score={data.score} recommendation={data.recommendation.display}>
                {renderReviewBlock(orderedStaff)}
                <hr />
                {renderReviewBlock(orderedNonStaff)}
            </ReviewBlock>
        </div>
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
