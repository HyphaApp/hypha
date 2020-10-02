import React, { useState }from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import LoadingPanel from '@components/LoadingPanel'
import SidebarBlock from '@components/SidebarBlock'
import ReviewBlock, { Review, AssignedToReview, Opinion } from '@components/ReviewBlock'
import { getSubmissionOfID, getReviewButtonStatus, getReviewDraftStatus } from '@selectors/submissions'
import { toggleReviewFormAction, setCurrentReviewAction } from '@actions/submissions'
import {deleteReviewAction} from './ReviewForm/actions'
import { selectFieldsInfo } from './ReviewForm/selectors'
import { selectGeneralInfo } from './GeneralInfo/selectors'
import './ReviewInformation.scss';





const ReviewInformation = ({ submission, submissionID, showReviewForm, toggleReviewForm, setCurrentReview, deleteReview, reviewDraftStatus, selectFieldsInfo, selectGeneralInfo }) => {
    const [showExternal, setShowExternal] = useState(false)

    if (submission === undefined || !submission.review) {
        return <LoadingPanel />
    }
    const data = submission.review

    const staff = [];
    const nonStaff = [];
    const partner = [];
    Object.values(data.assigned).map(person => {
        if (person.isStaff) {
            staff.push(person)
        } else if(person.is_partner){
            partner.push(person)
        } else {
            nonStaff.push(person)
        }
    })

    const orderPeople = (people) => {
        people.sort((a,b) => {
            if (a.role.order === null) {
                return 100;
            } else if (b.role.order === null) {
                return -1;
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

                if (!review ) {
                    return <AssignedToReview key={reviewer.id + '-no-review'} author={reviewer.name} userName={selectGeneralInfo && selectGeneralInfo.user ? selectGeneralInfo.user.email : ""}/>
                }

                return <Review
                    key={reviewer.id}
                    url={review.url}
                    id = {review.id}
                    author={reviewer.name}
                    icon={reviewer.role.icon}
                    score={review.score}
                    toggleReviewForm = {toggleReviewForm}
                    setCurrentReview = {setCurrentReview}
                    submissionID = {submissionID}
                    deleteReview={deleteReview}
                    selectFieldsInfo={selectFieldsInfo}
                    userName={selectGeneralInfo.user.email}
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


    const renderNormal = (people) => {
        const [peopleReviewed, peopleNotReviewed] = orderPeople(people);
        return <>
            {renderReviewBlock(peopleReviewed)}
            {renderReviewBlock(peopleNotReviewed)}
        </>
    }

    const renderCollapsed = (people) => {
        const [peopleReviewed, peopleNotReviewed] = orderPeople(people);
        return <>
            { renderReviewBlock(peopleReviewed) }
            { peopleNotReviewed.length !== 0 &&
            <div className="assigned-reviewers">
              <a  onClick={() => setShowExternal(!showExternal)}>{showExternal ? "Hide assigned reviewers": "All assigned reviewers"}</a>
              </div>
            }
            { showExternal &&
              renderReviewBlock(peopleNotReviewed)
            }
        </>
    }

    const hasSubmittedReview = submission.review.reviews.some(review => review.userId == selectGeneralInfo.user.id)

    return (
        <SidebarBlock title="Reviews &amp; assignees">
            { partner.length === 0 && staff.length === 0 && nonStaff.length === 0 && <h5>No reviews available</h5>}
            <ReviewBlock score={data.score} recommendation={data.recommendation.display}>
                { renderNormal(staff) }
                {staff.length !== 0 && partner.length !== 0 && <hr />}
                { renderNormal(partner) }
                {(partner.length !== 0 || staff.length !== 0) && nonStaff.length !== 0 && <hr />}
                { renderCollapsed(nonStaff) }

                <div className="wrapper wrapper--sidebar-buttons">
                  {!hasSubmittedReview && !reviewDraftStatus &&<>
                      <button onClick = {() =>  toggleReviewForm(true)} className="button button--primary button--half-width">Add a Review</button>
                  </> }
                  {!hasSubmittedReview && reviewDraftStatus && <>
                      <button onClick = {() => toggleReviewForm(true)} className="button button--primary button--half-width">Update Draft</button>
                  </>}

                  {data.reviews.length !== 0 &&  <>
                        <a 
                          href={`/apply/submissions/${submissionID}/reviews/`} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="button button--white button--half-width">View all</a>
                        <hr />
                  </>}
              </div>
            </ReviewBlock>

        </SidebarBlock>
    )
}

ReviewInformation.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number.isRequired,
    showReviewForm: PropTypes.bool,
    reviewDraftStatus: PropTypes.bool,
    toggleReviewForm: PropTypes.func,
    setCurrentReview: PropTypes.func,
    deleteReview: PropTypes.func,
    selectFieldsInfo: PropTypes.object,
    selectGeneralInfo: PropTypes.object
}



const mapStateToProps = (state, ownProps) => ({
    submission: getSubmissionOfID(ownProps.submissionID)(state),
    showReviewForm: getReviewButtonStatus(state),
    reviewDraftStatus: getReviewDraftStatus(state),
    selectFieldsInfo: selectFieldsInfo(state),
    selectGeneralInfo: selectGeneralInfo(state)
})

const mapDispatchToProps = (dispatch) => ({
    toggleReviewForm: (status) => dispatch(toggleReviewFormAction(status)),
    setCurrentReview: (reviewId) => dispatch(setCurrentReviewAction(reviewId)),
    deleteReview: (reviewId, submissionID) => dispatch(deleteReviewAction(reviewId, submissionID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ReviewInformation)
