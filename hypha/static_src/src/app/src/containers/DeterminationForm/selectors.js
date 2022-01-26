import {createSelector} from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
    state.DeterminationFormContainer ? state.DeterminationFormContainer : initialState;

export const selectFieldsInfo = createSelector(selectFieldsRenderer, domain => domain);
