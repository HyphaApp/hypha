import {createSelector} from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
    state.ReminderForm ? state.ReminderForm : initialState;

export const selectReminderForm = createSelector(selectFieldsRenderer, domain => domain);
