import * as ActionTypes from './constants';

export const initializeAction = (id, determinationId = null) => ({
    type: ActionTypes.INITIALIZE,
    id,
    determinationId
});


export const getDeterminationFieldsSuccessAction = (data) => ({
    type: ActionTypes.GET_DETERMINATION_FIELDS_SUCCESS,
    data
});

export const getDeterminationValuesSuccessAction = (data) => ({
    type: ActionTypes.GET_DETERMINATION_VALUES_SUCCESS,
    data
});

export const submitDeterminationAction = (determinationData, id) => ({
    type: ActionTypes.SUBMIT_DETERMINATION_DATA,
    id,
    determinationData
});

export const updateDeterminationAction = (determinationData, id, determinationId) => ({
    type: ActionTypes.UPDATE_DETERMINATION_DATA,
    id,
    determinationData,
    determinationId
});

export const deleteDeterminationAction = (determinationId, id) => ({
    type: ActionTypes.DELETE_DETERMINATION_DATA,
    id,
    determinationId
});

export const showLoadingAction = () => ({
    type: ActionTypes.SHOW_LOADING
});

export const hideLoadingAction = () => ({
    type: ActionTypes.HIDE_LOADING
});

export const clearInitialValues = () => ({
    type: ActionTypes.CLEAR_INITIAL_VALUES
});

export const toggleSaveDraftAction = (status) => ({
    type: ActionTypes.TOGGLE_SAVE_DRAFT,
    status
});
