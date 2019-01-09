import React from 'react';
import PropTypes from 'prop-types';


export default class SubmissionsByRoundListItem extends React.Component {
    render() {
        return (
            <li>
                <a>{this.props.title}</a>
            </li>
        );
    }
}

SubmissionsByRoundListItem.propTypes = {
    title: PropTypes.string,
};
