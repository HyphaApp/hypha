import {createSelector} from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
    state.FlagContainer ? state.FlagContainer : initialState;

export const selectFlagContainerInfo = createSelector(selectFieldsRenderer, domain => domain);
