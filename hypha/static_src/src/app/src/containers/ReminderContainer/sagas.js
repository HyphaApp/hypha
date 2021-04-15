import {
  call,
  put,
  takeLatest,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils'

export function* remindersFetch(action) {
  
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(apiFetch, {path : `/v1/submissions/${action.submissionID}/reminders/`});
    let data = yield response.json()
    yield put(
      Actions.getRemindersSuccessAction(data),
    );
    yield put(Actions.hideLoadingAction())
  } catch (e) {
    yield put(Actions.hideLoadingAction())
  }
}


export function* deleteReminder(action) {
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(apiFetch,
      {
      path : `/v1/submissions/${action.submissionID}/reminders/${action.reminderID}/`,
      method : "DELETE"
    })
    let data = yield response.json()
    yield put(
      Actions.getRemindersSuccessAction(data),
    );
    yield put(Actions.hideLoadingAction())
  }catch (e) {
    yield put(Actions.hideLoadingAction())
  }
}

export default function* reminderContainerSaga() {
  yield takeLatest(ActionTypes.INITIALIZE, remindersFetch);
  yield takeLatest(ActionTypes.DELETE_REMINDER, deleteReminder)
}
