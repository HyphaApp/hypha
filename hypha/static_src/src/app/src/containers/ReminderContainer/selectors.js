import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.ReminderContainer ? state.ReminderContainer : initialState;

export const selectReminderContainer = createSelector(selectFieldsRenderer, domain => domain);

export const selectReminders = createSelector(selectReminderContainer, domain => {
  let reminders = []
  domain.reminders && domain.reminders.map(reminder => {
      const existingReminderIndex = reminders.findIndex(r => r.grouper == reminder.action_type);
      if (existingReminderIndex != -1) {
        reminders[existingReminderIndex].list.push(reminder)
      } else {
        // new reminder.
        reminders.push({ grouper: reminder.action_type, list: [reminder] })
    }
  })
  return reminders
})
