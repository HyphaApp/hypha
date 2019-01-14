import React from 'react';
import PropTypes from 'prop-types';


export default class SubmissionsByRoundListItem extends React.Component {
    render() {
        return (
            <li className="listing__item">
                <a className="listing__link">{this.props.title}</a>
            </li>
        );
    }
}

SubmissionsByRoundListItem.propTypes = {
    title: PropTypes.string,
};
