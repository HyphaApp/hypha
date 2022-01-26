import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const reminderFormReducer = (state = initialState, action) => {
    switch (action.type) {
        case ActionTypes.FETCH_FIELDS_SUCCESS:
            return state.set('metaStructure', action.fields);
        case ActionTypes.SHOW_LOADING:
            return state.set('loading', true);
        case ActionTypes.HIDE_LOADING:
            return state.set('loading', false);
        default:
            return state;
    }
};

export default reminderFormReducer;
