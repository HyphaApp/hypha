import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.ReviewFormContainer ? state.ReviewFormContainer : initialState;

export const selectFieldsInfo = createSelector(selectFieldsRenderer, domain => domain);
