import React from 'react';
import Modal from 'react-modal';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import { MESSAGE_TYPES, addMessage } from '@actions/messages';
import { executeSubmissionAction } from '@actions/submissions';
import Select from '@components/Select'
import { getSubmissionOfID } from '@selectors/submissions';
import { redirect } from '@utils';

import './ReactModal.scss';
import './StatusActions.scss';

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

    customModalStyles = {
        overlay: {
            backgroundColor: 'rgba(30, 30, 30, 0.79)',
            zIndex: '200',
        },
        content: {
            top: '50%',
            left: '50%',
            right: 'auto',
            bottom: 'auto',
            transform: 'translate(-50%, -50%)',
            width: '90%',
            maxWidth: '650px',
            padding: '0',
            border: '0',
            borderRadius: '0',
        }
    };

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
            <div className="react-modal">
                <h4 className="react-modal__header-bar">Update status</h4>
                <div className="react-modal__inner">
                    <button className="react-modal__close" onClick={this.closeStatusModal}>&#10005;</button>
                    {executionActionError && <p>{executionActionError}</p>}
                    {phase && <p>Current status: {phase}</p>}
                    <div className="form form__select">
                        <Select
                            onChange={statusSelectValue => this.setState({
                                statusSelectValue
                            })}
                            options={submission.actions}
                            />
                    </div>
                    <button className="button button--primary button--top-space" onClick={this.handleStatusChange} disabled={this.formDisabled}>Progress</button>
                </div>
            </div>
        );
    }

    render() {
        const { submission } = this.props;

        if (submission === undefined || submission.actions === undefined) {
            return null;
        } else if (submission.actions.length === 0) {
            return (
                <div className="status-actions">
                    <button className="button button--primary button--full-width is-disabled" disabled={true}>Update status</button>
                </div>
            )
        }

        return (
            <>
                <Modal isOpen={this.state.modalVisible}
                    onRequestClose={this.closeStatusModal}
                    contentLabel="Update status"
                    style={this.customModalStyles}
                >
                    {this.renderModal()}
                </Modal>

                <div className="status-actions">
                    <button className="button button--primary button--full-width" onClick={this.openStatusModal}>Update status</button>
                </div>
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
