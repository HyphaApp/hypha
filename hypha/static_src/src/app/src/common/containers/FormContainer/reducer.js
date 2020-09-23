import initialState, {formInitialState} from './models';
import * as ActionTypes from './constants';


const FormReducer = (
    state = formInitialState,
    action
) => {
    switch(action.type) {
        case ActionTypes.UPDATE_FIELD_VALUE:
            return state
                .set('readyToSubmit', false)
                .setIn(
                    ['values', action.fieldName], 
                    action.fieldValue);
        case ActionTypes.ADD_VALIDATION_ERROR:
            if (action.errorMessage){
                return state.setIn(
                    ['errors', action.fieldName],
                    action.errorMessage);
            }
            else {
                return state.set('errors', state.errors.without(action.fieldName))
            }
        case ActionTypes.CLEAR_VALIDATION_ERRORS:
            return state.set('errors', {});
        case ActionTypes.VALIDATE_AND_SUBMIT_FORM:
            return state.set('readyToSubmit', true);
        default:
            return state;
    }
}

const FormContainerReducer = (
    state = initialState,
    action
) => {
    switch (action.type) {
        case ActionTypes.INITIALIZE_FORM:
            return state
                .setIn(['forms', action.formId], action.form);
        case ActionTypes.UPDATE_FIELD_VALUE:
        case ActionTypes.VALIDATE_AND_SUBMIT_FORM:
        case ActionTypes.CLEAR_VALIDATION_ERRORS:
        case ActionTypes.ADD_VALIDATION_ERROR:
            return state
                .setIn(
                    ['forms', action.formId],
                    FormReducer(state.forms[action.formId], action)
                );
        default:
            return state;
    }
}


export default FormContainerReducer;
