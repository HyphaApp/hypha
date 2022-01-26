import * as ActionTypes from './constants';

export const fetchFieldsSuccessAction = (fields) => ({
    type: ActionTypes.FETCH_FIELDS_SUCCESS,
    fields
});

export const fetchFieldsAction = (submissionID) => ({
    type: ActionTypes.FETCH_FIELDS,
    submissionID
});

export const createReminderAction = (values, submissionID) => ({
    type: ActionTypes.CREATE_REMINDER,
    values,
    submissionID
});

export const showLoadingAction = () => ({
    type: ActionTypes.SHOW_LOADING
});

export const hideLoadingAction = () => ({
    type: ActionTypes.HIDE_LOADING
});
