import React from 'react';
import PropTypes from 'prop-types';


export default class SubmissionsByRoundListHeading extends React.Component {
    render() {
        return (
            <li>
                <h2>{this.props.title} ({this.props.count})</h2>
            </li>
        );
    }
}

SubmissionsByRoundListHeading.propTypes = {
    title: PropTypes.string,
    count: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
    ]),
};
