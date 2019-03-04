import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types';
import { connect } from 'react-redux'
import useInterval from '@rooks/use-interval'

import { loadCurrentSubmission } from '@actions/submissions'
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
} from '@selectors/submissions'
import SubmissionDisplay from '@components/SubmissionDisplay';

const loadData = props => {
    return props.loadCurrentSubmission(['questions'], { bypassCache: true })
}

const hasChanged = (prevSubmission, submission, keys) => {
    return keys.some(key => {
        return JSON.stringify(prevSubmission[key]) !== JSON.stringify(submission[key])
    })
}

const hasContentUpdated = (prevSubmission, submission) => {
    return hasChanged(prevSubmission, submission, ['metaQuestions', 'questions'])

}


const  CurrentSubmissionDisplay = props => {
    const { submission, submissionID } = props

    const { start, stop } = useInterval(() => loadData(props), 30000)

    const [initialSubmissionLoaded, setInitialSubmissionLoaded] = useState(false)
    const [localSubmission, setSubmission] = useState(undefined);
    const [updated, setUpdated] = useState(false);
    const [updateMessage, setUpdateMessage] = useState('')

    // Load newly selected submission.
    useEffect(() => {
        setInitialSubmissionLoaded(false)
        setUpdated(false)
        setSubmission(undefined)
        loadData(props)
        start()

        return () => stop()
    }, [submissionID])

    // Determine if the submission has been updated by someone else.
    useEffect(() => {
        if (!submission || !submission.questions || submission.isFetching) {
            return;
        }

        if (submissionID !== submission.id) {
            return
        }

        if (!initialSubmissionLoaded) {
            setInitialSubmissionLoaded(true)
            setSubmission(submission)
        } else if (hasContentUpdated(localSubmission, submission)) {
            setUpdated(true)
            setUpdateMessage('The contents of this application have been changed by someone else.')
        }
    }, [submission])

    const handleUpdateSubmission = () => {
        setSubmission(submission)
        setUpdated(false)
    }

    if ( !localSubmission ) {
        return <p>Loading</p>
    }

    const renderUpdatedMessage = () =>{
        return <p>
            {updateMessage}
            <button onClick={handleUpdateSubmission}>Show updated</button>
        </p>
    }

    return <>
        {updated && renderUpdatedMessage()}
        <SubmissionDisplay
                submission={localSubmission}
                isLoading={!localSubmission || localSubmission.isFetching}
                isError={localSubmission && localSubmission.isErrored} />
    </>
}

CurrentSubmissionDisplay.propTypes = {
    submission: PropTypes.object,
    submissionID: PropTypes.number,
}

const mapStateToProps = state => ({
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
})

const mapDispatchToProps = dispatch => ({
    loadCurrentSubmission: (fields, options) => dispatch(loadCurrentSubmission(fields, options))
})


export default connect(mapStateToProps, mapDispatchToProps)(CurrentSubmissionDisplay)
