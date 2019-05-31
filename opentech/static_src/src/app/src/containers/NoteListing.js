import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import useInterval from "@rooks/use-interval"

import { fetchNewNotesForSubmission, editingNote } from '@actions/notes';
import Listing from '@components/Listing';
import NoteListingItem from '@components/NoteListingItem';
import {
    getNotesErrorState,
    getNotesErrorMessage,
    getNotesForSubmission,
    getNotesFetchState,
    getDraftNoteForSubmission,
} from '@selectors/notes';


const NoteListing = ({ loadNotes, submissionID, notes, isErrored, errorMessage, isLoading, editing, editNote }) => {
    const fetchNotes = () => loadNotes(submissionID)

    const {start, stop } = useInterval(fetchNotes, 30000)

    useEffect( () => {
        if ( submissionID ) {
            fetchNotes()
            start()
        } else {
            stop()
        }
    }, [submissionID])


    const handleRetry = () => {
        if (!isLoading || isErrored) {
            fetchNotes()
        }
    }

    /* const time = new Date(date).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}); */

    const orderedNotes = notes.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));

    const renderItem = note => {
        const date = new Date(note.timestamp).toLocaleDateString('en-gb', {day: 'numeric', month: 'short', year:'numeric', timezone:'GMT'})
        const edited = (
            note.edited ?
            new Date(note.edited).toLocaleDateString('en-gb', {day: 'numeric', month: 'short', year:'numeric', timezone:'GMT'})
            : null
        )

        return <NoteListingItem
            author={note.user}
            timestamp={date}
            key={`note-${note.id}`}
            message={note.message}
            submissionID={submissionID}
            disabled={!!editing}
            editable={note.editable}
            edited={edited}
            handleEditNote={() => editNote(note.id, note.message, submissionID)}
        />;
    }

    return (
        <Listing
            isLoading={ isLoading }
            isErrored={ isErrored }
            errorMessage={ errorMessage }
            handleRetry={ handleRetry }
            renderItem={ renderItem }
            items={ orderedNotes }
            column="notes"
        />
    );
}

NoteListing.propTypes = {
    loadNotes: PropTypes.func,
    editNote: PropTypes.func,
    submissionID: PropTypes.number,
    notes: PropTypes.array,
    isErrored: PropTypes.bool,
    errorMessage: PropTypes.string,
    isLoading: PropTypes.bool,
    editing: PropTypes.object,
};


const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNewNotesForSubmission(submissionID)),
    editNote: (id, message, submissionID) => dispatch(editingNote(id, message, submissionID)),
});

const mapStateToProps = (state, ownProps) => ({
    notes: getNotesForSubmission(ownProps.submissionID)(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
    errorMessage: getNotesErrorMessage(state),
    editing: getDraftNoteForSubmission(ownProps.submissionID)(state),

});

export default connect(mapStateToProps, mapDispatchToProps)(NoteListing);
