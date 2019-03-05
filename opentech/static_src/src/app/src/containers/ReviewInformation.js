import React, { useState }from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import LoadingPanel from '@components/LoadingPanel'
import SidebarBlock from '@components/SidebarBlock'
import ReviewBlock, { Review, AssignedToReview, Opinion } from '@components/ReviewBlock'

import { getSubmissionOfID } from '@selectors/submissions'


const ReviewInformation = ({ submission }) => {
    const [showExternal, setShowExternal] = useState(false)

    if (submission === undefined || !submission.review) {
        return <LoadingPanel />
    }
    const data = submission.review

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
            data.reviews.find(review => person.id === review.authorId) ? hasReviewed.push(person) : notReviewed.push(person);
        });

        const notOpinionated = notReviewed.filter(
            person => !data.reviews.find(
                review => review.opinions.find(
                    opinion => opinion.authorId === person.id
                )
            )
        )

        return [hasReviewed, notOpinionated];
    }

    const renderReviewBlock = (reviewers) => {
        return <>
            {reviewers.map(reviewer => {
                const review = data.reviews.find(review => review.authorId === reviewer.id);

                if (!review) {
                    return <AssignedToReview key={reviewer.id + '-no-review'} author={reviewer.name} />
                }

                return <Review
                    key={reviewer.id}
                    url={review.url}
                    author={reviewer.name}
                    icon={reviewer.role.icon}
                    score={review.score}
                    recommendation={review.recommendation} >
                    {review.opinions.map((opinion, i) => {
                        const author = data.assigned.find(person => person.id === opinion.authorId);
                        return <Opinion
                            key={i}
                            author={author.name}
                            icon={author.role.icon}
                            opinion={opinion.opinion}
                        />
                    })}
                </Review>
            })}
        </>
    }

    const [staffReviewed, staffNotReviewed] = orderPeople(staff);
    const [nonStaffReviewed, nonStaffNotReviewed] = orderPeople(nonStaff);

    return (
        <SidebarBlock title="Reviews &amp; assignees">
            <ReviewBlock score={data.score} recommendation={data.recommendation.display}>
                {renderReviewBlock(staffReviewed)}
                {renderReviewBlock(staffNotReviewed)}
                <hr />
                { renderReviewBlock(nonStaffReviewed) }
                { nonStaffNotReviewed.length !== 0 &&
                  <a onClick={() => setShowExternal(!showExternal)}>{showExternal ? "Hide assigned reviewers": "All assigned reviewers"}</a>
                }
                { showExternal &&
                    renderReviewBlock(nonStaffNotReviewed)
                }
            </ReviewBlock>
        </SidebarBlock>
    )
}

ReviewInformation.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number.isRequired,
}

const mapStateToProps = (state, ownProps) => ({
    submission: getSubmissionOfID(ownProps.submissionID)(state),
})

export default connect(mapStateToProps)(ReviewInformation)
