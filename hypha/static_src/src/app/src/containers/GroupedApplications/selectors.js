import {createSelector} from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
    state.GroupedApplications ? state.GroupedApplications : initialState;

export const SelectGroupedApplicationsInfo = createSelector(selectFieldsRenderer, domain => domain);
