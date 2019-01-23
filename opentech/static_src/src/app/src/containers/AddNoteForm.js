import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { createNoteForSubmission } from '@actions/notes';
import RichTextForm from '@components/RichTextForm';

class AddNoteForm extends React.Component {
    static propTypes = {
        submitNote: PropTypes.func,
        submissionID: PropTypes.number,
    };

    state = {
        text: '',
    };

    render() {
        return (
            <>
                <RichTextForm onValueChange={this.setText} />
                <button onClick={this.onSubmit}>Submit</button>
            </>
        );
    }

    onSubmit = () => {
        this.props.submitNote(this.props.submissionID, {
            message: this.state.text,
            visibility: 'internal',
        });
    }

    setText = text => {
        this.setState({
            text: text.trim(),
        });
    }
}

const mapDispatchToProps = dispatch => ({
    submitNote: (submissionID, note) => dispatch(createNoteForSubmission(submissionID, note)),
});

export default connect(null, mapDispatchToProps)(AddNoteForm);
