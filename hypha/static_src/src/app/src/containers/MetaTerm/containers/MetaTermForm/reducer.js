import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const metaFormReducer = (state = initialState, action) => {
    switch (action.type) {
        case ActionTypes.GET_META_TERMS_SUCCESS:
            return state.set('metaTermsStructure', action.data);
        case ActionTypes.SHOW_LOADING:
            return state.set('loading', true);
        case ActionTypes.HIDE_LOADING:
            return state.set('loading', false);
        case ActionTypes.SET_SELECTED_META_TERMS:
            return state.set('selectedMetaTerms', action.data);
        default:
            return state;
    }
};

export default metaFormReducer;
