import React from 'react'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'

import SidebarBlock from '@components/SidebarBlock'
import { getSubmissionOfID } from '@selectors/submissions'


const ScreeningOutcome = ({ submission }) => {
    const outcome = submission && submission.screening;
    return <SidebarBlock title="Screening Outcome">
        {  outcome ? outcome : "Not yet screened"}
    </SidebarBlock>
}

ScreeningOutcome.propTypes = {
    submission: PropTypes.object,
}

const mapStateToProps = (state, ownProps) => ({
    submission: getSubmissionOfID(ownProps.submissionID)(state),
})

export default connect(mapStateToProps)(ScreeningOutcome)
