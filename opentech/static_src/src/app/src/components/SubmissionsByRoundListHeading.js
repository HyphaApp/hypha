import React from 'react';
import PropTypes from 'prop-types';
import './SubmissionsByRoundListHeading.scss';


export default class SubmissionsByRoundListHeading extends React.Component {
    render() {
        return (
            <li className="submission-list-item submission-list-item--heading">
                <h5 className="submission-list-item__title">{this.props.title}</h5>
                <span className="submission-list-item__count">{this.props.count}</span>
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
