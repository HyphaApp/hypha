import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { MESSAGE_TYPES, addMessage } from '@actions/messages';
import { executeSubmissionAction } from '@actions/submissions';
import Modal from '@components/Modal';
import { getSubmissionOfID } from '@selectors/submissions';
import { redirect } from '@utils';

class StatusActions extends React.Component {
    static propTypes = {
        submissionID: PropTypes.number.isRequired,
        submission: PropTypes.shape({
            id: PropTypes.number,
            phase: PropTypes.string,
            actions: PropTypes.arrayOf(PropTypes.shape({
                display: PropTypes.string.isRequired,
                value: PropTypes.string.isRequired,
            })),
        }),
        changeStatus: PropTypes.func.isRequired,
        addMessage: PropTypes.func.isRequired,
    }

    state = {
        modalVisible: false,
        statusSelectValue: '',
    }

    openStatusModal = () => {
        this.setState({
            modalVisible: true,
            statusSelectValue: '',
        });
    }

    closeStatusModal = () => {
        this.setState({
            modalVisible: false,
            statusSelectValue: '',
        });
    }

    handleStatusChange = () => {
        const { addMessage, changeStatus, submission } = this.props
        const { statusSelectValue } = this.state
        const actionObject = submission.actions.find(
            v => v.value === statusSelectValue
        )

        switch (actionObject.type) {
            case 'redirect':
                return redirect(actionObject.target)
            case 'submit':
                return changeStatus(statusSelectValue)
                        .then(() => {
                            this.closeStatusModal()
                            addMessage(
                                'You have successfully updated the status of the submission',
                                MESSAGE_TYPES.SUCCESS,
                            );
                        })
            default:
                throw "Invalid action type"
        }
    }

    renderModal = () => {
        const { submission } = this.props
        const { phase } = submission
        return (
            <>
                {phase && <div>Current status: {phase}</div>}
                <select value={this.state.statusSelectValue} onChange={evt => this.setState({ statusSelectValue: evt.target.value })}>
                    <option>---</option>
                    {submission.actions.map(({value, display}) =>
                        <option value={value} key={value}>{display}</option>
                    )}
                </select>
                <button onClick={this.handleStatusChange} disabled={!this.state.statusSelectValue}>Progress</button>
            </>
        );
    }

    render() {
        const { submission } = this.props;

        if (submission === undefined || submission.actions === undefined || submission.actions.length === 0) {
            return null;
        }

        return (
            <div>
                <Modal visible={this.state.modalVisible} onClose={this.closeStatusModal} heading="Update status" content={this.renderModal()} />
                <button onClick={this.openStatusModal}>Update status</button>
            </div>
        );
    }
}

const mapStateToProps = (state, ownProps) => ({
    submission: getSubmissionOfID(ownProps.submissionID)(state),
});

const mapDispatchToProps = (dispatch, ownProps) => ({
    changeStatus: action => {
        return dispatch(executeSubmissionAction(ownProps.submissionID, action))
    },
    addMessage: (message, type) => dispatch(addMessage(message, type)),
});

export default connect(mapStateToProps, mapDispatchToProps)(StatusActions);
