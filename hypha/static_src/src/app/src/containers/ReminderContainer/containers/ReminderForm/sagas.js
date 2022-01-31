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
import {toggleModalAction} from '@containers/ReminderContainer/actions';


export function* fetchFields(action) {
    try {
        yield put(Actions.showLoadingAction());
        let response = yield call(apiFetch, {path: `/v1/submissions/${action.submissionID}/reminders/fields/`});
        let data = yield response.json();
        yield put(
            Actions.fetchFieldsSuccessAction(data),
        );
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export function* createReminder(action) {
    try {
        yield put(Actions.showLoadingAction());
        yield call(
            apiFetch,
            {
                path: `/v1/submissions/${action.submissionID}/reminders/`,
                method: 'POST',
                options: {
                    body: JSON.stringify(action.values)
                }
            }
        );
        let response = yield call(apiFetch, {
            path: `/v1/submissions/${action.submissionID}/`
        });
        response = yield response.json();
        let data = yield camelizeKeys(response);
        yield put(
            updateSubmissionReminderAction(action.submissionID, data.reminders)
        );
        yield put(toggleModalAction(false));
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export default function* reminderFormSaga() {
    yield takeLatest(ActionTypes.FETCH_FIELDS, fetchFields);
    yield takeLatest(ActionTypes.CREATE_REMINDER, createReminder);
}
