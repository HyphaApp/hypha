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
    getNoteIDsForSubmissionOfID,
    getNotesFetchState,
    getNoteEditingState
} from '@selectors/notes';


const NoteListing = ({ loadNotes, submissionID, noteIDs, isErrored, errorMessage, isLoading, editing }) => {
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

    const renderItem = noteID => <Note key={`note-${noteID}`} noteID={noteID} submissionID={submissionID} />;

    return (
        <Listing
            editing={editing}
            isLoading={ isLoading }
            isErrored={ isErrored }
            errorMessage={ errorMessage }
            handleRetry={ handleRetry }
            renderItem={ renderItem }
            items={ noteIDs }
            column="notes"
        />
    );
}

NoteListing.propTypes = {
    loadNotes: PropTypes.func,
    submissionID: PropTypes.number,
    noteIDs: PropTypes.array,
    isErrored: PropTypes.bool,
    errorMessage: PropTypes.string,
    isLoading: PropTypes.bool,
    editing: PropTypes.object,
};


const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNewNotesForSubmission(submissionID)),
});

const mapStateToProps = (state, ownProps) => ({
    noteIDs: getNoteIDsForSubmissionOfID(ownProps.submissionID)(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
    errorMessage: getNotesErrorMessage(state),
    editing: getNoteEditingState(state),
});

export default connect(mapStateToProps, mapDispatchToProps)(NoteListing);
