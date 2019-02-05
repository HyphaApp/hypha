import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { createNoteForSubmission } from '@actions/notes';
import RichTextForm from '@components/RichTextForm';

import {
    getNoteCreatingErrorForSubmission,
    getNoteCreatingStateForSubmission,
} from '@selectors/notes';

import './AddNoteForm.scss';

class AddNoteForm extends React.Component {
    static propTypes = {
        submitNote: PropTypes.func,
        submissionID: PropTypes.number,
        error: PropTypes.any,
        isCreating: PropTypes.bool,
    };

    render() {
        const { error, isCreating } = this.props;
        return (
            <>
                {Boolean(error) && <p>{error}</p>}
                <RichTextForm
                    disabled={isCreating}
                    onSubmit={this.onSubmit}
                    instance="add-note-form"
                />
            </>
        );
    }

    onSubmit = (message, resetEditor) => {
        this.props.submitNote(this.props.submissionID, {
            message,
            visibility: 'internal',
        }).then(() => resetEditor());
    }
}

const mapStateToProps = (state, ownProps) => ({
    error: getNoteCreatingErrorForSubmission(ownProps.submissionID)(state),
    isCreating: getNoteCreatingStateForSubmission(ownProps.submissionID)(state),
});

const mapDispatchToProps = dispatch => ({
    submitNote: (submissionID, note) => dispatch(createNoteForSubmission(submissionID, note)),
});

export default connect(mapStateToProps, mapDispatchToProps)(AddNoteForm);
