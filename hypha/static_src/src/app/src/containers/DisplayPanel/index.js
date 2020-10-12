import React, { useEffect, useState } from 'react'
import { connect } from 'react-redux'
import PropTypes from 'prop-types'
import { withWindowSizeListener } from 'react-window-size-listener'

import { MESSAGE_TYPES, addMessage } from '@actions/messages'
import { clearCurrentSubmission } from '@actions/submissions'
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getReviewButtonStatus,
    getCurrentReview
} from '@selectors/submissions'
import { getDraftNoteForSubmission } from '@selectors/notes';

import CurrentSubmissionDisplay from '@containers/CurrentSubmissionDisplay'
import ReviewInformation from '@containers/ReviewInformation'
import ScreeningOutcome from '@containers/ScreeningOutcome'
import AddNoteForm from '@containers/AddNoteForm'
import NoteListing from '@containers/NoteListing'
import StatusActions from '@containers/StatusActions'
import Tabber, {Tab} from '@components/Tabber'
import SubmissionLink from '@components/SubmissionLink';
import ReviewFormContainer from '@containers/ReviewForm';


import './style.scss'
// {!showReviewForm ? <CurrentSubmissionDisplay /> : <ReviewFormContainer submissionID={submissionID}/> }


const DisplayPanel = props => {
    const { submissionID, submission, addMessage, showReviewForm, currentReview} = props
    const [ currentStatus, setCurrentStatus ] = useState(undefined)
    const [ localSubmissionID, setLocalSubmissionID ] = useState(submissionID)

    useEffect(() => {
        setCurrentStatus(undefined)
        setLocalSubmissionID(submissionID)
    }, [submissionID])

    useEffect(() => {
        if (localSubmissionID !== submissionID) {
            return
        }

        if (!submission || !submission.status) {
            setCurrentStatus(undefined)
            return
        }

        const { status, changedLocally } = submission

        if (currentStatus && status !== currentStatus && !changedLocally) {
            addMessage(
                'The status of this application has changed by another user.',
                MESSAGE_TYPES.INFO
            )
        }

        setCurrentStatus(status)
    })

    const { windowSize: { windowWidth: width }, clearSubmission, draftNote } = props;
    const isMobile = width < 1024;
    const isEditing = !!draftNote && !!draftNote.id;

    let tabs = [
        <Tab button="Status" key="status">
            <ScreeningOutcome submissionID={submissionID} />
            <StatusActions submissionID={submissionID} />
            <ReviewInformation submissionID={submissionID} />
            <SubmissionLink submissionID={submissionID} />
        </Tab>,
        <Tab button="Notes" key="note">
            <NoteListing submissionID={submissionID} />
            {isEditing ? null : (
                    <AddNoteForm submissionID={submissionID} />
            )}
        </Tab>
    ]

    if ( isMobile ) {
        tabs = [
            <Tab button="Back" key="back" handleClick={ clearSubmission } />,
            <Tab button="Application" key="application">
                {showReviewForm ? <CurrentSubmissionDisplay /> : <ReviewFormContainer submissionID={submissionID} reviewId={currentReview}/>}  
            </Tab>,
            ...tabs
        ]
    }
 
    return (
        showReviewForm ? <ReviewFormContainer submissionID={submissionID} reviewId={currentReview}/>  :
        <div className="display-panel">

            { !isMobile && (
                <div className="display-panel__column">
                    <div className="display-panel__header display-panel__header--spacer"></div>
                    <div className="display-panel__body display-panel__body--center">
                        
                         <CurrentSubmissionDisplay /> 
                    </div>
                </div>
            )}

            <div className="display-panel__column">
                <div className="display-panel__body">
                
                    <Tabber>
                        { tabs }
                    </Tabber>
             
                </div>
            </div>
        </div>
    

    )
}

DisplayPanel.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number,
    loadSubmission: PropTypes.func,
    clearSubmission: PropTypes.func.isRequired,
    windowSize: PropTypes.objectOf(PropTypes.number),
    addMessage: PropTypes.func,
    draftNote: PropTypes.object,
    showReviewForm: PropTypes.bool,
    currentReview: PropTypes.number
}

const mapStateToProps = (state, ownProps) => ({
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
    showReviewForm: getReviewButtonStatus(state),
    currentReview: getCurrentReview(state),
    draftNote: getDraftNoteForSubmission(getCurrentSubmissionID(state))(state),
})

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission,
    addMessage: addMessage,
}

export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DisplayPanel));
