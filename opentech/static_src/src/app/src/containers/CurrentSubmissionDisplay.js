import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import { loadCurrentSubmission } from '@actions/submissions'
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
} from '@selectors/submissions'
import SubmissionDisplay from '@components/SubmissionDisplay';

const loadData = props => {
    props.loadCurrentSubmission(['questions'])

}

class CurrentSubmissionDisplay extends React.Component {
    static propTypes = {
        submission: PropTypes.object,
        submissionID: PropTypes.number,
    }

    componentDidMount() {
        loadData(this.props)
    }

    componentDidUpdate(prevProps) {
        if (this.props.submissionID !== prevProps.submissionID ) {
            loadData(this.props)
        }
    }

    render () {
        const { submission } = this.props
        if ( !submission ) {
            return <p>Loading</p>
        }
        return <SubmissionDisplay
                   submission={submission}
                   isLoading={submission.isFetching}
                   isError={submission.isErrored} />
    }

}

const mapStateToProps = state => ({
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
})


export default connect(mapStateToProps, {loadCurrentSubmission})(CurrentSubmissionDisplay)
