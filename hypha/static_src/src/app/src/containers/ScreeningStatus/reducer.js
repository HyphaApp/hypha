import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const screeningInfoReducer = (state = initialState, action) => {
    switch (action.type) {
        case ActionTypes.SHOW_LOADING:
            return state.set('loading', true);
        case ActionTypes.HIDE_LOADING:
            return state.set('loading', false);
        case ActionTypes.GET_SCREENING_STATUSES:
            return state.set('screeningStatuses', action.data);
        case ActionTypes.SET_DEFAULT_VALUE:
            return state.set('defaultSelectedValue', action.data);
        case ActionTypes.SET_VISIBLE_OPTION:
            return state.set('selectedValues', action.data);
        default:
            return state;
    }
};

export default screeningInfoReducer;
