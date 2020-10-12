import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.GeneralInfoContainer ? state.GeneralInfoContainer : initialState;

export const selectGeneralInfo = createSelector(selectFieldsRenderer, domain => domain);
