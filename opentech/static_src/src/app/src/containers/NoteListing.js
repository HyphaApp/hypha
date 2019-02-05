import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { CSSTransition } from 'react-transition-group';

import { fetchNotesForSubmission } from '@actions/notes';
import Listing from '@components/Listing';
import Note from '@containers/Note';
import {
    getNotesErrorState,
    getNoteIDsForSubmissionOfID,
    getNotesFetchState,
} from '@selectors/notes';

class NoteListing extends React.Component {
    static propTypes = {
        loadNotes: PropTypes.func,
        submissionID: PropTypes.number,
        noteIDs: PropTypes.array,
        isErrored: PropTypes.bool,
        isLoading: PropTypes.bool,
    };

    componentDidUpdate(prevProps) {
        const { isLoading, loadNotes, submissionID } = this.props;
        const prevSubmissionID = prevProps.submissionID;

        if(
            submissionID !== null && submissionID !== undefined &&
            prevSubmissionID !== submissionID && !isLoading
        ) {
            loadNotes(submissionID);
        }
    }

    componentDidMount() {
        const { isLoading, loadNotes, submissionID } = this.props;

        if (submissionID && !isLoading) {
            loadNotes(submissionID);
        }
    }

    handleRetry = () => {
        if (this.props.isLoading || !this.props.isErrored) {
            return;
        }
        this.props.loadNotes(this.props.submissionID);
    }

    renderItem = noteID => {
        return (
            <CSSTransition key={`note-${noteID}`} timeout={200} classNames="add-note">
                <Note key={`note-${noteID}`} noteID={noteID} />
            </CSSTransition>
        );
    }

    render() {
        const { noteIDs } = this.props;
        const passProps = {
            isLoading: this.props.isLoading,
            isError: this.props.isErrored,
            handleRetry: this.handleRetry,
            renderItem: this.renderItem,
            items: noteIDs,
        };
        return (
            <Listing {...passProps} column="notes" />
        );
    }
}

const mapDispatchToProps = dispatch => ({
    loadNotes: submissionID => dispatch(fetchNotesForSubmission(submissionID)),
});

const mapStateToProps = (state, ownProps) => ({
    noteIDs: getNoteIDsForSubmissionOfID(ownProps.submissionID)(state),
    isLoading: getNotesFetchState(state),
    isErrored: getNotesErrorState(state),
});

export default connect(mapStateToProps, mapDispatchToProps)(NoteListing);
