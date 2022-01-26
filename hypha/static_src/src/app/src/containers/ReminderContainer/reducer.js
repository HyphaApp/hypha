import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const reminderContainerReducer = (state = initialState, action) => {
    switch (action.type) {
        case ActionTypes.SHOW_LOADING:
            return state.set('loading', true);
        case ActionTypes.HIDE_LOADING:
            return state.set('loading', false);
        case ActionTypes.TOGGLE_MODAL:
            return state.set('isModalOpened', action.data);
        default:
            return state;
    }
};

export default reminderContainerReducer;
