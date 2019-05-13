import React from 'react';
import PropTypes from 'prop-types';

import './styles.scss';

export default class NoteListingItem extends React.Component {
    static propTypes = {
        user: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        timestamp: PropTypes.string.isRequired,
        handleEditNote: PropTypes.func.isRequired,
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
        const { timestamp, message, handleEditNote } = this.props;

        return (
            <li className="note">
                <p className="note__meta">
                    <span className="note__meta note__meta--inner">
                        <span>{this.parseUser()}</span>
                        <a onClick={() => handleEditNote()} className="note__edit" href="#">
                            Edit
                            <svg className="icon icon--pen"><use xlinkHref="#pen"></use></svg>
                        </a>
                    </span>

                    <span className="note__date">{timestamp}</span>
                </p>
                <div className="note__content" dangerouslySetInnerHTML={{__html: message}} />
            </li>
        );
    }
}
