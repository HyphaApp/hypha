import React from 'react';
import Modal from 'react-modal';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { MESSAGE_TYPES, addMessage } from '@actions/messages';
import { executeSubmissionAction } from '@actions/submissions';
import Select from '@components/Select'
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
            isExecutingAction: PropTypes.bool,
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

    get formDisabled() {
        return (
            !this.state.statusSelectValue ||
            Boolean(this.props.submission.isExecutingAction)
        )
    }

    renderModal = () => {
        const { submission } = this.props
        const { phase, executionActionError } = submission

        return (
            <>
                <button onClick={this.closeStatusModal}>[X]</button>
                {executionActionError && <p>{executionActionError}</p>}
                {phase && <div>Current status: {phase}</div>}
                <Select
                    onChange={statusSelectValue => this.setState({
                        statusSelectValue
                    })}
                    options={submission.actions}
                />
                <button onClick={this.handleStatusChange} disabled={this.formDisabled}>Progress</button>
            </>
        );
    }

    render() {
        const { submission } = this.props;

        if (submission === undefined || submission.actions === undefined) {
            return null;
        } else if (submission.actions.length === 0) {
            return <button disabled={true}>Update status (no actions)</button>
        }

        return (
            <>
                <Modal isOpen={this.state.modalVisible}
                    onRequestClose={this.closeStatusModal}
                    contentLabel="Update status"
                >
                    {this.renderModal()}
                </Modal>
                <button onClick={this.openStatusModal}>Update status</button>
            </>
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
