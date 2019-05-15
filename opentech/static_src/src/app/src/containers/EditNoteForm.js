import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { editNoteForSubmission, handleRemoveNote } from '@actions/notes';
import { removeNoteFromSubmission } from '@actions/submissions';
import RichTextForm from '@components/RichTextForm';

import {
    getNoteCreatingErrorForSubmission,
    getNoteCreatingStateForSubmission,
} from '@selectors/notes';

import './AddNoteForm.scss';

class EditNoteForm extends React.Component {
    static propTypes = {
        submitNote: PropTypes.func,
        submissionID: PropTypes.number,
        error: PropTypes.any,
        isCreating: PropTypes.bool,
        note: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
        editing: PropTypes.object,
        updateNotes: PropTypes.func,
        removeEditedNote: PropTypes.func,
        removeNoteFromSubmission: PropTypes.func,
    };

    render() {
        const { error, isCreating, editing } = this.props;

        return (
            <>
                {Boolean(error) && <p>{error}</p>}
                <RichTextForm
                    disabled={isCreating}
                    onSubmit={this.onSubmit}
                    instance="add-note-form"
                    editing={editing}
                />
            </>
        );
    }

    onSubmit = (message, resetEditor) => {
        this.props.submitNote({
            ...this.props.editing,
            message,
        }).then(() => {
            this.props.removeNoteFromSubmission(this.props.submissionID, this.props.editing);
            this.props.removeEditedNote(this.props.submissionID, this.props.editing);
        });
    }
}

const mapStateToProps = (state, ownProps) => ({
    error: getNoteCreatingErrorForSubmission(ownProps.submissionID)(state),
    isCreating: getNoteCreatingStateForSubmission(ownProps.submissionID)(state),
});

const mapDispatchToProps = (dispatch, ownProps) => ({
    submitNote: (note) => dispatch(editNoteForSubmission(note)),
    removeEditedNote: (submissionID, note) => dispatch(handleRemoveNote(submissionID, note)),
    removeNoteFromSubmission: (submissionID, note) => dispatch(removeNoteFromSubmission(submissionID, note)),
});

export default connect(mapStateToProps, mapDispatchToProps)(EditNoteForm);
