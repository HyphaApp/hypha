import React from 'react';
import PropTypes from 'prop-types';

import './styles.scss';

export default class NoteListingItem extends React.Component {
    static propTypes = {
        user: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        timestamp: PropTypes.string.isRequired,
    };

    parseUser() {
        const { user } = this.props;

        if (user.length > 16) {
            return `${user.substring(0, 16)}...`
        } else {
            return user;
        }
    }

    render() {
        const { timestamp, message } = this.props;

        return (
            <li className="note">
                <p className="note__meta">
                    <span>{this.parseUser()}</span>
                    <span className="note__date">{timestamp}</span>
                </p>
                <div className="note__content" dangerouslySetInnerHTML={{__html: message}} />
            </li>
        );
    }
}
