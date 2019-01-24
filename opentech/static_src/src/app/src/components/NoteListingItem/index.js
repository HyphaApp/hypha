import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

import './styles.scss';

export default class NoteListingItem extends React.Component {
    static propTypes = {
        user: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        timestamp: PropTypes.instanceOf(moment).isRequired,
    };

    render() {
        const { user, timestamp, message } = this.props;
        return (
            <li className="note">
                <p className="note__meta">
                    <span>{user}</span>
                    <span className="note__date">{timestamp.format('ll')}</span>
                </p>
                <div className="note__content" dangerouslySetInnerHTML={{__html: message}} />
            </li>
        );
    }
}
