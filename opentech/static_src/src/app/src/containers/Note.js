import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { getNoteOfID } from '@selectors/notes';
import NoteListingItem from '@components/NoteListingItem';
import { handleEditNote } from '@actions/notes';

class Note extends React.Component {
    static propTypes = {
        handleEditNote: PropTypes.func,
        submissionID: PropTypes.number,
        note: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
    };

    render() {
        const { note, handleEditNote } = this.props;

        const date = new Date(note.timestamp).toLocaleDateString('en-gb', {day: 'numeric', month: 'short', year:'numeric', timezone:'GMT'})

        return <NoteListingItem
                user={note.user}
                message={note.message}
                timestamp={date}
                handleEditNote={() => handleEditNote(note.message)}
        />;
    }
}

const mapStateToProps = (state, ownProps) => ({
    note: getNoteOfID(ownProps.noteID)(state),
});

const mapDispatchToProps = (dispatch, ownProps) => ({
    handleEditNote: (message) => dispatch(handleEditNote(ownProps.noteID, ownProps.submissionID, message)),
})

export default connect(mapStateToProps, mapDispatchToProps)(Note);
