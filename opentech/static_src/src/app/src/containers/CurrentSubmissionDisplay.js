import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types';
import { connect } from 'react-redux'
import useInterval from '@rooks/use-interval'
import pick from 'lodash.pick'
import isEqual from 'lodash.isequal'

import { loadCurrentSubmission } from '@actions/submissions'
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
} from '@selectors/submissions'
import SubmissionDisplay from '@components/SubmissionDisplay';

const loadData = props => {
    return props.loadCurrentSubmission(['questions'], { bypassCache: true })
}

const hasSubmissionUpdated = (prevSubmission, submission) => {
    const KEYS_MONITORED = ['metaQuestions', 'questions', 'stage']
    const pickKeys = obj => pick(obj, KEYS_MONITORED)
    return !isEqual(...[submission, prevSubmission].map(v => pickKeys(v)))

}

const  CurrentSubmissionDisplay = props => {
    const { submission, submissionID } = props

    const { start, stop } = useInterval(() => loadData(props), 30000)

    const [initialSubmissionLoaded, setInitialSubmissionLoaded] = useState(false)
    const [localSubmission, setSubmission] = useState(undefined);
    const [submissionUpdated, setSubmissionUpdated] = useState(false);

    // Load newly selected submission.
    useEffect(() => {
        setInitialSubmissionLoaded(false)
        setSubmissionUpdated(false)
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

        if (!initialSubmissionLoaded) {
            setInitialSubmissionLoaded(true)
            setSubmission(submission)
            setSubmissionUpdated(false)
        } else if (hasSubmissionUpdated(localSubmission, submission)) {
            setSubmissionUpdated(true)
        }
    }, [submission])

    const handleUpdateSubmission = () => {
        setSubmission(submission)
        setSubmissionUpdated(false)
    }

    if ( !localSubmission ) {
        return <p>Loading</p>
    }

    const renderUpdatedMessage = () =>{
        if (!submissionUpdated) {
            return null
        }
        const msg = (
            'The contents of this application have been changed by someone ' +
            ' else.'
        )
        return <p>
            {msg} <button onClick={handleUpdateSubmission}>Show updated</button>
        </p>
    }

    return <>
        {renderUpdatedMessage()}
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
