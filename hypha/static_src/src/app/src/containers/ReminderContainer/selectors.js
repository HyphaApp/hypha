import {createSelector} from 'reselect';
import initialState from './models';
import {getSubmissionReminders, getCurrentSubmission} from '@redux/selectors/submissions';

export const selectFieldsRenderer = state =>
    state.ReminderContainer ? state.ReminderContainer : initialState;

export const selectReminderContainer = createSelector(selectFieldsRenderer, domain => domain);

export const selectRemindersLoading = createSelector([selectReminderContainer, getCurrentSubmission], (domain, currentSubmission) => {
    return domain.loading || typeof currentSubmission == 'undefined' || typeof currentSubmission.reminders == 'undefined';
});

export const selectReminders = createSelector(getSubmissionReminders, submissionReminders => {
    let reminders = [];
    submissionReminders.map(reminder => {
        const existingReminderIndex = reminders.findIndex(r => r.grouper == reminder.actionType);
        if (existingReminderIndex != -1) {
            reminders[existingReminderIndex].list.push(reminder);
        }
        else {
        // new reminder.
            reminders.push({grouper: reminder.actionType, list: [reminder]});
        }
    });
    return reminders;
});
