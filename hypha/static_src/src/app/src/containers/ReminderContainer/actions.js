import * as ActionTypes from './constants';

export const initializeAction = (submissionID) => ({
  type: ActionTypes.INITIALIZE,
  submissionID
});

export const deleteReminderAction = (submissionID, reminderID) => ({
  type: ActionTypes.DELETE_REMINDER,
  submissionID,
  reminderID
});

export const getRemindersSuccessAction = (data) => ({
  type: ActionTypes.GET_REMINDERS_SUCCESS,
  data
});

export const showLoadingAction = () => ({
  type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
  type: ActionTypes.HIDE_LOADING,
})
