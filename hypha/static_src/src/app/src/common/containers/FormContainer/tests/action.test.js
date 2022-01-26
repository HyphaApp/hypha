import * as actions from '../actions';
import * as ActionTypes from '../constants';
import Reducer from '../reducer';

describe('Test actions of form container', () => {

    it('Should return the intialize action type', () => {
        const formId = 1;
        const form = {title: 'form1'};
        const expectedResult = {
            type: ActionTypes.INITIALIZE_FORM,
            formId,
            form
        };
        const action = actions.initializeFormAction(formId, form);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the update Field Value action type', () => {
        const formId = 1;
        const fieldName = 'form1';
        const fieldValue = 'value';
        const expectedResult = {
            type: ActionTypes.UPDATE_FIELD_VALUE,
            formId,
            fieldName,
            fieldValue
        };
        const action = actions.updateFieldValueAction(formId, fieldName, fieldValue);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the add Validation Error Action type', () => {
        const formId = 1;
        const fieldName = 'form1';
        const errorMessage = 'This is an error msg';
        const expectedResult = {
            type: ActionTypes.ADD_VALIDATION_ERROR,
            formId,
            fieldName,
            errorMessage
        };
        const action = actions.addValidationErrorAction(formId, fieldName, errorMessage);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear Validation Error Action type', () => {
        const formId = 1;
        const expectedResult = {
            type: ActionTypes.CLEAR_VALIDATION_ERRORS,
            formId
        };
        const action = actions.clearValidationErrorAction(formId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the destroy Form Action type', () => {
        const formId = 1;
        const expectedResult = {
            type: ActionTypes.DESTROY_FORM,
            formId
        };
        const action = actions.destroyFormAction(formId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the validate And Submit FormAction type', () => {
        const formId = 1;
        const expectedResult = {
            type: ActionTypes.VALIDATE_AND_SUBMIT_FORM,
            formId
        };
        const action = actions.validateAndSubmitFormAction(formId);
        expect(action).toEqual(expectedResult);
    });

});
