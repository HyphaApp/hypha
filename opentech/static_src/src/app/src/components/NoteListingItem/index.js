import React from 'react';
import PropTypes from 'prop-types';

import './styles.scss';

export default class NoteListingItem extends React.Component {
    static propTypes = {
        author: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        timestamp: PropTypes.string.isRequired,
        handleEditNote: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        editable: PropTypes.bool,
    };

    parseUser() {
        const { author } = this.props;

        if (author.length > 16) {
            return `${author.substring(0, 16)}...`
        } else {
            return author;
        }
    }

    render() {
        const { timestamp, message, handleEditNote, disabled, editable} = this.props;


        return (
            <li className={`note ${disabled ? 'disabled' : ''}`}>
                <p className="note__meta">
                    <span className="note__meta note__meta--inner">
                        <span>{this.parseUser()}</span>
                        { editable &&
                            <a onClick={(e) => handleEditNote(e.preventDefault())} className="note__edit" href="#">
                                Edit
                                <svg className="icon icon--pen"><use xlinkHref="#pen"></use></svg>
                            </a>
                        }
                    </span>

                    <span className="note__date">{timestamp}</span>
                </p>
                <div className="note__content" dangerouslySetInnerHTML={{__html: message}} />
            </li>
        );
    }
}
