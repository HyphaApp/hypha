import React from 'react'
import injectReducer from '@utils/injectReducer'
import injectSaga from '@utils/injectSaga'
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import { bindActionCreators, compose } from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
import * as Selectors from './selectors';
import "./styles.scss";
import { SidebarBlock } from '@components/SidebarBlock'
import LoadingPanel from '@components/LoadingPanel';
import Modal from '@material-ui/core/Modal';
import { withStyles } from '@material-ui/core/styles';
import ReminderList from './components/ReminderList';
import ReminderForm from './containers/ReminderForm' 


const styles = {
    modal: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
  };

class ReminderContainer extends React.PureComponent {

    state = {
        open : false
    }

    componentDidUpdate(prevProps) {
        if(this.props.submissionID != prevProps.submissionID) {
            this.props.initAction(this.props.submissionID)
        }
    }

    handleModalClose = () => {
        this.setState({open : false})
    }

    render(){
        const { classes } = this.props;
        if(this.props.reminderInfo.loading) return <LoadingPanel /> 
        return (
            <div className="reminder-container">
                <SidebarBlock title={"Reminders"}>
                    <div className="status-actions">
                        <button 
                            className="button button--primary button--half-width button--bottom-space reminder-button" 
                            onClick={() => this.setState({open : true})}
                        >
                            Create Reminder
                        </button>
                        <Modal
                            className={classes.modal} 
                            open={this.state.open}
                        >
                            <>
                                <ReminderForm
                                    submissionID={this.props.submissionID} 
                                    closeForm={() => this.setState({open: false})}
                                />
                            </>
                        </Modal>
                        {this.props.reminders.length
                        ?
                        this.props.reminders.map(reminders =>
                        <ReminderList
                            key={reminders.grouper}
                            title={reminders.grouper}
                            reminders={reminders.list} 
                            submissionID={this.props.submissionID} 
                            deleteReminder={this.props.deleteReminder}
                        />)
                        :
                        <div>No reminders yet.</div>}
                    </div>
                </SidebarBlock>
            </div>
        )
    }
}

ReminderContainer.propTypes = {
    reminderInfo: PropTypes.object,
    initAction: PropTypes.func,
    deleteReminder: PropTypes.func,
    classes: PropTypes.object,
    submissionID: PropTypes.number,
    reminders: PropTypes.array
}

const mapStateToProps = state =>  ({
    reminderInfo : Selectors.selectReminderContainer(state),
    reminders: Selectors.selectReminders(state)
});
  
  
function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        initAction: Actions.initializeAction,
        deleteReminder: Actions.deleteReminderAction,
    },
    dispatch,
    );
}
  
const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);
  
const withReducer = injectReducer({ key: 'ReminderContainer', reducer });
const withSaga = injectSaga({ key: 'ReminderContainer', saga });
  
  
export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
    withStyles(styles)
)(ReminderContainer);
