import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';

export default class NotesPanelItem extends React.Component {
    static propTypes = {
        note: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
    };

    render() {
        const { note } = this.props;

        return (
            <div>
                <div style={{fontWeight: 'bold'}}>{note.user} - {moment(note.timestamp).format('ll')}</div>
                <div>{note.message}</div>
            </div>
        );
    }
}
