import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const determinationFormReducer = (state = initialState, action) => {
    switch (action.type) {
        case ActionTypes.GET_DETERMINATION_FIELDS_SUCCESS:
            return state.set('metaStructure', action.data).set('initialValues', null);
        case ActionTypes.SHOW_LOADING:
            return state.set('loading', true);
        case ActionTypes.HIDE_LOADING:
            return state.set('loading', false);
        case ActionTypes.GET_DETERMINATION_VALUES_SUCCESS:
            return state.set('initialValues', action.data);
        case ActionTypes.CLEAR_INITIAL_VALUES:
            return state.set('initialValues', null);
        case ActionTypes.TOGGLE_SAVE_DRAFT:
            return state.set('saveAsDraft', action.status);
        default:
            return state;
    }
};

export default determinationFormReducer;
