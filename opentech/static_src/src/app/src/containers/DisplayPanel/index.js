import React, { useEffect, useState } from 'react'
import { connect } from 'react-redux'
import PropTypes from 'prop-types'
import { withWindowSizeListener } from 'react-window-size-listener'

import { MESSAGE_TYPES, addMessage } from '@actions/messages'
import { clearCurrentSubmission } from '@actions/submissions'
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
} from '@selectors/submissions'

import CurrentSubmissionDisplay from '@containers/CurrentSubmissionDisplay'
import ReviewInformation from '@containers/ReviewInformation'
import AddNoteForm from '@containers/AddNoteForm'
import NoteListing from '@containers/NoteListing'
import StatusActions from '@containers/StatusActions'
import Tabber, {Tab} from '@components/Tabber'
import SubmissionLink from '@components/SubmissionLink';

import './style.scss'


const DisplayPanel = props => {
    const { submissionID, submission, addMessage} = props
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

    const { windowSize: {windowWidth: width}  } = props;
    const { clearSubmission } = props;

    const isMobile = width < 1024;
    const submissionLink = "/apply/submissions/" + submissionID + "/";

    let tabs = [
        <Tab button="Notes" key="note">
            <NoteListing submissionID={submissionID} />
            <AddNoteForm submissionID={submissionID} />
        </Tab>,
        <Tab button="Status" key="status">
            <StatusActions submissionID={submissionID} />
            <ReviewInformation submissionID={submissionID} />
            <SubmissionLink submissionID={submissionID} />
        </Tab>
    ]

    if ( isMobile ) {
        tabs = [
            <Tab button="Back" key="back" handleClick={ clearSubmission } />,
            <Tab button="Application" key="application">
                <CurrentSubmissionDisplay />
            </Tab>,
            ...tabs
        ]
    }

    return (
        <div className="display-panel">
            { !isMobile && (
                <div className="display-panel__column">
                    <div className="display-panel__header display-panel__header--spacer"></div>
                    <div className="display-panel__body display-panel__body--center">
                        <a target="_blank" rel="noopener noreferrer" href={ submissionLink }>Open in new tab</a>
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
}

const mapStateToProps = state => ({
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
})

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission,
    addMessage: addMessage,
}

export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DisplayPanel));
