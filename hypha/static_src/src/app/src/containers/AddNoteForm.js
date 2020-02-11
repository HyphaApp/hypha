import React, { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import {
    removedStoredNote,
    writingNote,
} from '@actions/notes';
import { getDraftNoteForSubmission } from '@selectors/notes';
import { createNoteForSubmission } from '@actions/notes';
import RichTextForm from '@components/RichTextForm';

import {
    getNoteCreatingErrorForSubmission,
    getNoteCreatingStateForSubmission,
} from '@selectors/notes';

import './AddNoteForm.scss';


const AddNoteForm = ({error, isCreating, draftNote, submitNote, storeNote, clearNote, submissionID}) => {
    const [initialValue, updateInitialValue] = useState()

    useEffect(() => {
        updateInitialValue(draftNote && draftNote.message || '')
    }, [submissionID])

    const onSubmit = (message, resetEditor) => {
        submitNote(submissionID, {
            message,
            visibility: 'team',
        }).then(() => resetEditor());
    }

    return (
        <>
            {Boolean(error) && <p>{error}</p>}
            <RichTextForm
                initialValue={initialValue}
                disabled={isCreating}
                onCancel={() => clearNote(submissionID)}
                onChange={(message) => storeNote(submissionID, message)}
                onSubmit={onSubmit}
                instance="add-note-form"
            />
        </>
    );
}


AddNoteForm.propTypes = {
    submitNote: PropTypes.func,
    storeNote: PropTypes.func,
    clearNote: PropTypes.func,
    submissionID: PropTypes.number,
    error: PropTypes.any,
    draftNote: PropTypes.object,
    isCreating: PropTypes.bool,
    removeEditedNote: PropTypes.func,
};



const mapStateToProps = (state, ownProps) => ({
    error: getNoteCreatingErrorForSubmission(ownProps.submissionID)(state),
    isCreating: getNoteCreatingStateForSubmission(ownProps.submissionID)(state),
    draftNote: getDraftNoteForSubmission(ownProps.submissionID)(state),
});

const mapDispatchToProps = dispatch => ({
    submitNote: (submissionID, note) => dispatch(createNoteForSubmission(submissionID, note)),
    storeNote: (submissionID, message) => dispatch(writingNote(submissionID, message)),
    clearNote: (submissionID) => dispatch(removedStoredNote(submissionID)),
});

export default connect(mapStateToProps, mapDispatchToProps)(AddNoteForm);
