import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.SubmissionFiltersContainer ? state.SubmissionFiltersContainer : initialState;

export const SelectSubmissionFiltersInfo = createSelector(selectFieldsRenderer, domain => domain);

export const SelectSelectedFilters = createSelector(selectFieldsRenderer, domain => domain.filterQuery)
