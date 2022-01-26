import {
    call,
    put,
    takeLatest
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import {apiFetch} from '@api/utils';
import {updateSubmissionReminderAction} from '@redux/actions/submissions';
import {camelizeKeys} from 'humps';

export function* deleteReminder(action) {
    try {
        yield put(Actions.showLoadingAction());
        yield call(apiFetch,
            {
                path: `/v1/submissions/${action.submissionID}/reminders/${action.reminderID}/`,
                method: 'DELETE'
            });
        let response = yield call(apiFetch, {
            path: `/v1/submissions/${action.submissionID}/`
        });
        response = yield response.json();
        let data = yield camelizeKeys(response);
        yield put(
            updateSubmissionReminderAction(action.submissionID, data.reminders)
        );
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export default function* reminderContainerSaga() {
    yield takeLatest(ActionTypes.DELETE_REMINDER, deleteReminder);
}
