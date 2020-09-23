import * as ActionTypes from './constants';

export const initializeFormAction = (formId, form) => ({
    type: ActionTypes.INITIALIZE_FORM,
    formId,
    form
});

export const updateFieldValueAction = (formId, fieldName, fieldValue) => ({
    type: ActionTypes.UPDATE_FIELD_VALUE,
    formId,
    fieldName,
    fieldValue
});

export const addValidationErrorAction = (formId, fieldName, errorMessage) => ({
    type: ActionTypes.ADD_VALIDATION_ERROR,
    formId,
    fieldName,
    errorMessage
});


export const clearValidationErrorAction = formId => ({
    type: ActionTypes.CLEAR_VALIDATION_ERRORS,
    formId
});


export const destroyFormAction = formId => ({
    type: ActionTypes.DESTROY_FORM,
    formId
});


export const validateAndSubmitFormAction = formId => ({
    type: ActionTypes.VALIDATE_AND_SUBMIT_FORM,
    formId
});
