import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.ReminderContainer ? state.ReminderContainer : initialState;

export const selectReminderContainer = createSelector(selectFieldsRenderer, domain => domain);
