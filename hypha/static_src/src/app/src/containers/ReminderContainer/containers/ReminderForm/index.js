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
import FormContainer from '@common/containers/FormContainer';
import './styles.scss';
import LoadingPanel from '@components/LoadingPanel';


class ReminderForm extends React.PureComponent {

    componentDidMount() {
        this.props.fetchFieldsAction(this.props.submissionID);
    }

    getMetaFields() {
        let metaFieldsActions = [{
            text: 'Cancel',
            type: 'secondary',
            callback: () => this.props.closeForm()
        },
        {
            text: 'Create',
            type: 'primary',
            callback: (values) => {this.props.createReminderAction(values, this.props.submissionID);}
        }

        ];

        return {
            fields: this.props.reminderForm.metaStructure,
            actions: metaFieldsActions,
            initialValues: null,
            title: 'Create Reminder',
            style: {paddingLeft: '30px'}
        };
    }

    render() {
        if (this.props.reminderForm.loading) {return <LoadingPanel />;}
        return (
            <div className="reminder-form">
                {this.props.reminderForm.metaStructure && this.props.reminderForm.metaStructure.length != 0 &&
                <FormContainer metadata={this.getMetaFields()} formId={'ReminderForm'} />
                }
            </div>
        );
    }
}

ReminderForm.propTypes = {
    fetchFieldsAction: PropTypes.func,
    submissionID: PropTypes.number,
    closeForm: PropTypes.func,
    reminderForm: PropTypes.object,
    createReminderAction: PropTypes.func
};

const mapStateToProps = state => ({
    reminderForm: Selectors.selectReminderForm(state)
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        fetchFieldsAction: Actions.fetchFieldsAction,
        createReminderAction: Actions.createReminderAction
    },
    dispatch,
    );
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({key: 'ReminderForm', reducer});
const withSaga = injectSaga({key: 'ReminderForm', saga});


export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
)(ReminderForm);
