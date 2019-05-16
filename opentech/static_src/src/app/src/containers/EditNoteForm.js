import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import {
    editNoteForSubmission,
    removedStoredNote,
    writingNote,
} from '@actions/notes';
import {
    getDraftNoteForSubmission,
    getNoteCreatingErrorForSubmission,
    getNoteCreatingStateForSubmission,
} from '@selectors/notes';
import RichTextForm from '@components/RichTextForm';

import './AddNoteForm.scss';

class EditNoteForm extends React.Component {
    static propTypes = {
        submissionID: PropTypes.number,
        error: PropTypes.any,
        isCreating: PropTypes.bool,
        draftNote: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
        submitNote: PropTypes.func,
        storeNote: PropTypes.func,
        clearNote: PropTypes.func,
    };

    render() {
        const { error, isCreating, draftNote, clearNote, submissionID} = this.props;

        return (
            <>
                {Boolean(error) && <p>{error}</p>}
                <RichTextForm
                    disabled={isCreating}
                    onSubmit={this.onSubmit}
                    onCancel={() => clearNote(submissionID)}
                    instance="add-note-form"
                    initialValue={draftNote.message}
                />
            </>
        );
    }

    onSubmit = (message, resetEditor) => {
        this.props.submitNote({
            ...this.props.draftNote,
            message,
        }, this.props.submissionID);
    }
}

const mapStateToProps = (state, ownProps) => ({
    error: getNoteCreatingErrorForSubmission(ownProps.submissionID)(state),
    isCreating: getNoteCreatingStateForSubmission(ownProps.submissionID)(state),
    draftNote: getDraftNoteForSubmission(ownProps.submissionID)(state),
});

const mapDispatchToProps = (dispatch, ownProps) => ({
    submitNote: (note, submissionID) => dispatch(editNoteForSubmission(note, submissionID)),
    storeNote: (submissionID, message) => dispatch(writingNote(submissionID, message)),
    clearNote: (submissionID) => dispatch(removedStoredNote(submissionID)),
});

export default connect(mapStateToProps, mapDispatchToProps)(EditNoteForm);
