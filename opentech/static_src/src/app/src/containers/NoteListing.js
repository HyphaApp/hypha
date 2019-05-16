import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import useInterval from "@rooks/use-interval"

import { fetchNewNotesForSubmission } from '@actions/notes';
import Listing from '@components/Listing';
import Note from '@containers/Note';
import {
    getNotesErrorState,
    getNotesErrorMessage,
    getNotesForSubmission,
    getNotesFetchState,
    getDraftNoteForSubmission,
} from '@selectors/notes';


const NoteListing = ({ loadNotes, submissionID, notes, isErrored, errorMessage, isLoading, editing }) => {
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

    const orderedNotes = notes.sort((a,b) => a.timestamp - b.timestamp);

    const renderItem = note => <Note key={`note-${note.id}`} noteID={note.id} submissionID={submissionID} disabled={!!editing} />;

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
    submissionID: PropTypes.number,
    notes: PropTypes.array,
    isErrored: PropTypes.bool,
    errorMessage: PropTypes.string,
    isLoading: PropTypes.bool,
    editing: PropTypes.object,
};


const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNewNotesForSubmission(submissionID)),
});

const mapStateToProps = (state, ownProps) => ({
    notes: getNotesForSubmission(ownProps.submissionID)(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
    errorMessage: getNotesErrorMessage(state),
    editing: getDraftNoteForSubmission(ownProps.submissionID)(state),
});

export default connect(mapStateToProps, mapDispatchToProps)(NoteListing);
