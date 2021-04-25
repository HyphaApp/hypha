import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.ReminderContainer ? state.ReminderContainer : initialState;

export const selectReminderContainer = createSelector(selectFieldsRenderer, domain => domain);

export const selectReminders = createSelector(selectReminderContainer, domain => {
  let reminders = []
  domain.reminders && domain.reminders.map(reminder => {
    if(reminders.find(r => r.grouper == reminder.action_type)){
      const index = reminders.indexOf(reminders.find(r => r.grouper == reminder.action_type))
      reminders[index].list.push(reminder)
    }
    else {
      reminders.push({
        grouper: reminder.action_type,
        list: [reminder]
      })
    }
  })
  return reminders
})
