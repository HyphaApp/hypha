import React from 'react'
import PropTypes from 'prop-types'

const Review = ({ review }) => {
    const { reviewUrl, author, score, recommendation } = review

    return (
        <p>
            <a href={reviewUrl}>
                {author} - {score} - {recommendation.display}
            </a>
        </p>
    )
}

Review.propTypes = {
    review: PropTypes.shape({
        author: PropTypes.string.isRequired,
        score: PropTypes.number.isRequired,
        recommendation: PropTypes.shape({
            display: PropTypes.string.isRequired,
        }).isRequired,
        reviewUrl: PropTypes.string.isRequired,
    }),
}

const ReviewsBlock = ({ submission }) => {
    if (submission.review === undefined) {
        return null
    }

    return (
        <div>
            <h1>Reviews &amp; assigness</h1>
            {submission.review.reviews.map(review =>
                <Review key={review.id} {...{ review }} />)}
        </div>
    )
}

ReviewsBlock.propTypes = {
    submission: PropTypes.shape({
        review: PropTypes.shape({
            reviews: PropTypes.arrayOf(PropTypes.shape({
                id: PropTypes.number,
            })),
        }),
    }),
}

export default ReviewsBlock
