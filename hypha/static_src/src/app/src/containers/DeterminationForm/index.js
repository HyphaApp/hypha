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
import {getCurrentDetermination} from '@selectors/submissions';
import * as Selectors from './selectors';
import './styles.scss';
import FormContainer from '@common/containers/FormContainer';
import LoadingPanel from '@components/LoadingPanel';
import {toggleDeterminationFormAction, clearCurrentDeterminationAction} from '../../redux/actions/submissions';


export class DeterminationFormContainer extends React.PureComponent {

    componentDidMount() {
        this.props.initializeAction(this.props.submissionID, this.props.determinationId ? this.props.determinationId : null);
    }

    getMetaFields() {

        let metaFieldsActions = [{
            text: 'back',
            type: 'secondary',
            callback: () => {this.props.toggleDeterminationForm(false); this.props.clearCurrentDetermination();}
        }];

        if (this.props.formData.saveAsDraft) {
            metaFieldsActions.push({
                text: 'Update Draft',
                type: 'secondary',
                callback: values => {
                    let newValues = {...values, is_draft: true};
                    this.props.submitDetermination(newValues, this.props.submissionID);
                }});
        }
        else if (!this.props.determinationId) {
            metaFieldsActions.push({
                text: 'Save Draft',
                type: 'secondary',
                callback: values => {
                    let newValues = {...values, is_draft: true};
                    this.props.submitDetermination(newValues, this.props.submissionID);
                }
            });
        }

        if (this.props.determinationId) {
            metaFieldsActions.push({
                text: 'Update',
                type: 'primary',
                callback: values => this.props.updateDetermination(values, this.props.submissionID, this.props.determinationId)
            });
        }
        else {
            metaFieldsActions.push({
                text: 'Create',
                type: 'primary',
                callback: values => this.props.submitDetermination(values, this.props.submissionID)
            });
        }


        return {
            fields: this.props.currentDetermination ? this.props.formData.metaStructure.filter(field => field.type !== 'TypedChoiceField') : this.props.formData.metaStructure,
            actions: metaFieldsActions,
            initialValues: this.props.formData.initialValues
        };
    }

    render() {
        return <div
            className={'determination-form-container'}>
            {this.props.determinationId ? <h3>Update Determination</h3> : <h3>Create Determination</h3> }
            {this.props.formData.loading ? <LoadingPanel /> : <>
                <FormContainer metadata={this.getMetaFields()} formId={'myIntialForm'} />
            </>}
        </div>;
    }
}

DeterminationFormContainer.propTypes = {
    formData: PropTypes.object,
    initializeAction: PropTypes.func,
    submitDetermination: PropTypes.func,
    deleteDetermination: PropTypes.func,
    updateDetermination: PropTypes.func,
    toggleDeterminationForm: PropTypes.func,
    toggleSaveDraft: PropTypes.func,
    submissionID: PropTypes.number,
    determinationId: PropTypes.number,
    clearCurrentDetermination: PropTypes.func,
    currentDetermination: PropTypes.number
};


export const mapStateToProps = state => ({
    formData: Selectors.selectFieldsInfo(state),
    currentDetermination: getCurrentDetermination(state)
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators(
        {
            initializeAction: Actions.initializeAction,
            submitDetermination: Actions.submitDeterminationAction,
            deleteDetermination: Actions.deleteDeterminationAction,
            updateDetermination: Actions.updateDeterminationAction,
            toggleDeterminationForm: toggleDeterminationFormAction,
            toggleSaveDraft: Actions.toggleSaveDraftAction,
            clearCurrentDetermination: clearCurrentDeterminationAction

        },
        dispatch,
    );
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({key: 'DeterminationFormContainer', reducer});
const withSaga = injectSaga({key: 'DeterminationFormContainer', saga});



export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
)(DeterminationFormContainer);
