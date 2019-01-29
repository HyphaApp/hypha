import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

export default class NoteListingItem extends React.Component {
    static propTypes = {
        user: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        timestamp: PropTypes.instanceOf(moment).isRequired,
    };

    render() {
        const { user, timestamp, message } = this.props;
        return (
            <div>
                <div style={{fontWeight: 'bold'}}>{user} - {timestamp.format('ll')}</div>
                <div dangerouslySetInnerHTML={{__html: message}} />
            </div>
        );
    }
}
