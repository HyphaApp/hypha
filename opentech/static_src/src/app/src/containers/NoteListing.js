import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { CSSTransition } from 'react-transition-group';

import useInterval from "@rooks/use-interval"

import { fetchNewNotesForSubmission } from '@actions/notes';
import Listing from '@components/Listing';
import Note from '@containers/Note';
import {
    getNotesErrorState,
    getNotesErrorMessage,
    getNoteIDsForSubmissionOfID,
    getNotesFetchState,
} from '@selectors/notes';


const NoteListing = ({loadNotes, submissionID, noteIDs, isErrored, errorMessage, isLoading }) => {
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

    const renderItem = noteID => {
        return (
            <CSSTransition key={`note-${noteID}`} timeout={200} classNames="add-note">
                <Note key={`note-${noteID}`} noteID={noteID} />
            </CSSTransition>
        );
    }

    return (
        <Listing
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
};


const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNewNotesForSubmission(submissionID)),
});

const mapStateToProps = (state, ownProps) => ({
    noteIDs: getNoteIDsForSubmissionOfID(ownProps.submissionID)(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
    errorMessage: getNotesErrorMessage(state),
});

export default connect(mapStateToProps, mapDispatchToProps)(NoteListing);
