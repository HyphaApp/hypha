import * as ActionTypes from './constants';

export const initializeAction = (searchParam) => ({
    type: ActionTypes.INITIALIZE,
    searchParam
});

export const getApplicationsSuccessAction = (data) => ({
    type: ActionTypes.GET_APPLICATIONS_SUCCESS,
    data
});

export const showLoadingAction = () => ({
    type: ActionTypes.SHOW_LOADING
});

export const hideLoadingAction = () => ({
    type: ActionTypes.HIDE_LOADING
});
