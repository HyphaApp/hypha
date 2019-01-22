import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { fetchNotesForSubmission } from '@actions/notes';
import NotesPanel from '@components/NotesPanel';
import NotesPanelItem from '@components/NotesPanelItem';
import {
    getNotesErrorState,
    getNotesForCurrentSubmission,
    getNotesFetchState,
} from '@selectors/notes';

class SubmissionNotesPanel extends React.Component {
    static propTypes = {
        loadNotes: PropTypes.func,
        submissionID: PropTypes.number,
        notes: PropTypes.array,
        isErrored: PropTypes.bool,
        isLoading: PropTypes.bool,
    };

    componentDidUpdate(prevProps) {
        const { submissionID } = this.props;
        const prevSubmissionID = prevProps.submissionID;

        if(
            submissionID !== null && submissionID !== undefined &&
            prevSubmissionID !== submissionID && !this.props.isLoading
        ) {
            this.props.loadNotes(submissionID);
        }
    }

    handleRetry = () => {
        if (this.props.isLoading || !this.props.isErrored) {
            return;
        }
        this.props.loadNotes(this.props.submissionID);
    }

    render() {
        const { notes } = this.props;
        const passProps = {
            isLoading: this.props.isLoading,
            isErrored: this.props.isErrored,
            handleRetry: this.handleRetry,
        };
        return (
            <NotesPanel {...passProps}>
                {notes.map(v =>
                    <NotesPanelItem key={`note-${v.id}`} note={v} />
                )}
            </NotesPanel>
        );
    }
}

const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNotesForSubmission(submissionID)),
});

const mapStateToProps = state => ({
    notes: getNotesForCurrentSubmission(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
});

export default connect(mapStateToProps, mapDispatchToProps)(SubmissionNotesPanel);
