import React from 'react';
import PropTypes from 'prop-types';

import './styles.scss';

const SubmissionLink = ({ submissionID }) => {
    const submissionLink = `/apply/submissions/${submissionID}/`;

    return (
        <div className="submission-link">
            <a target="_blank" rel="noopener noreferrer" href={submissionLink}>
                Open in new tab
                <svg><use xlinkHref="#open-in-new-tab"></use></svg>
            </a>
        </div>
    )
}

SubmissionLink.propTypes = {
    submissionID: PropTypes.number,
}

export default SubmissionLink;
