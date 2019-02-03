import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

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

        const date = new Date(note.timestamp).toLocaleDateString('en-gb', {day: 'numeric', month: 'short', year:'numeric'})

        return <NoteListingItem
                user={note.user}
                message={note.message}
                timestamp={date}
        />;
    }

}

const mapStateToProps = (state, ownProps) => ({
    note: getNoteOfID(ownProps.noteID)(state),
});

export default connect(mapStateToProps)(Note);
