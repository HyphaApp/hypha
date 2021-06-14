import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.MetaTermForm ? state.MetaTermForm : initialState;

export const selectMetaTermsInfo = createSelector(selectFieldsRenderer, domain => domain);
