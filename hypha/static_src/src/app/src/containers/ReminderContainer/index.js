import React from 'react';
import injectReducer from '@utils/injectReducer';
import injectSaga from '@utils/injectSaga';
import {withRouter} from 'react-router-dom';
import {connect} from 'react-redux';
import {bindActionCreators, compose} from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
import * as Selectors from './selectors';
import './styles.scss';
import {SidebarBlock} from '@components/SidebarBlock';
import LoadingPanel from '@components/LoadingPanel';
import Modal from '@material-ui/core/Modal';
import {withStyles} from '@material-ui/core/styles';
import ReminderList from './components/ReminderList';
import ReminderForm from './containers/ReminderForm';


const styles = {
    modal: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
    }
};

class ReminderContainer extends React.PureComponent {

    renderSubmissionReminders = () => {
        if (this.props.remindersLoading) {return <LoadingPanel/>;}

        if (this.props.reminders.length) {
            return this.props.reminders.map(reminder =>
                <ReminderList
                    key={reminder.grouper}
                    title={reminder.grouper}
                    reminders={reminder.list}
                    deleteReminder={this.props.deleteReminder}
                />);
        }
        else {return <div>No reminders yet.</div>;}
    };

    render() {
        const {classes} = this.props;
        return (
            <div className="reminder-container">
                <SidebarBlock title={'Reminders'}>
                    <div className="status-actions">
                        <button
                            className="button button--primary button--half-width button--bottom-space reminder-button"
                            onClick={() => this.props.toggleModal(true)}
                        >
                            Create Reminder
                        </button>
                        <Modal
                            className={classes.modal}
                            open={this.props.reminderInfo.isModalOpened}
                        >
                            <>
                                <ReminderForm
                                    submissionID={this.props.submissionID}
                                    closeForm={() => this.props.toggleModal(false)}
                                />
                            </>
                        </Modal>
                        {this.renderSubmissionReminders()}
                    </div>
                </SidebarBlock>
            </div>
        );
    }
}

ReminderContainer.propTypes = {
    reminderInfo: PropTypes.object,
    reminders: PropTypes.array,
    remindersLoading: PropTypes.bool,
    deleteReminder: PropTypes.func,
    toggleModal: PropTypes.func,
    classes: PropTypes.object,
    submissionID: PropTypes.number
};

const mapStateToProps = state => ({
    reminderInfo: Selectors.selectReminderContainer(state),
    reminders: Selectors.selectReminders(state),
    remindersLoading: Selectors.selectRemindersLoading(state)
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        deleteReminder: Actions.deleteReminderAction,
        toggleModal: Actions.toggleModalAction
    },
    dispatch,
    );
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({key: 'ReminderContainer', reducer});
const withSaga = injectSaga({key: 'ReminderContainer', saga});


export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
    withStyles(styles)
)(ReminderContainer);
