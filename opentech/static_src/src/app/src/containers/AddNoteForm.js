import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { createNoteForSubmission } from '@actions/notes';
import RichTextForm from '@components/RichTextForm';
import {
    getNoteCreatingErrorForSubmission,
    getNoteCreatingStateForSubmission,
} from '@selectors/notes';

class AddNoteForm extends React.Component {
    static propTypes = {
        submitNote: PropTypes.func,
        submissionID: PropTypes.number,
        error: PropTypes.any,
        isCreating: PropTypes.bool,
    };

    state = {
        text: '',
    };

    render() {
        const { error, isCreating } = this.props;
        return (
            <>
                {Boolean(error) && <p>{error}</p>}
                <RichTextForm
                    disabled={isCreating}
                    value={this.state.text}
                    onValueChange={this.setText} />
                <button
                    disabled={!this.state.text.trim() || isCreating}
                    onClick={this.onSubmit}
                >
                    Submit
                </button>
            </>
        );
    }

    onSubmit = async () => {
        const action = await this.props.submitNote(this.props.submissionID, {
            message: this.state.text.trim(),
            visibility: 'internal',
        });
        if (action === true) {
            this.setState({
                text: ''
            });
        }
    }

    setText = text => {
        this.setState({
            text
        });
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
