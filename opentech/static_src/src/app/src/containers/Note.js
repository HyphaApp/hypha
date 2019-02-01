import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import moment from 'moment';

import { getNoteOfID } from '@selectors/notes';
import NoteListingItem from '@components/NoteListingItem';

class Note extends React.Component {
    static propTypes = {
        note: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
    };

    render() {
        const { note } = this.props;

        return <NoteListingItem
                user={note.user}
                message={note.message}
                timestamp={moment(note.timestamp)}
        />;
    }

}

const mapStateToProps = (state, ownProps) => ({
    note: getNoteOfID(ownProps.noteID)(state),
});

export default connect(mapStateToProps)(Note);
