import {
    call,
    put,
    takeLatest
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import {toggleDeterminationFormAction} from '../../redux/actions/submissions';
import {apiFetch} from '@api/utils';

export function* initialFetch(action) {

    try {
        yield put(Actions.showLoadingAction());
        let response = yield call(apiFetch, {path: `/v1/submissions/${action.id}/determinations/fields/`});
        let data = yield response.json();
        yield put(
            Actions.getDeterminationFieldsSuccessAction(data),
        );
        let url = `/v1/submissions/${action.id}/determinations/draft/`;

        if (action.determinationId !== null) {
            url = `/v1/submissions/${action.id}/determinations/${action.determinationId}`;
        }

        response = yield call(apiFetch, {path: url});
        data = yield response.json();
        if (data) {
            yield put(Actions.toggleSaveDraftAction(data.is_draft));
        }
        yield put(Actions.getDeterminationValuesSuccessAction(data));
        yield put(Actions.hideLoadingAction());

    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export function* submitDetermination(action) {
    const url = `/v1/submissions/${action.id}/determinations/`;
    try {
        yield put(Actions.showLoadingAction());
        yield call(
            apiFetch,
            {
                path: url,
                method: 'POST',
                options: {
                    body: JSON.stringify(action.determinationData)
                }
            }
        );
        yield put(toggleDeterminationFormAction(false));
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export function* updateDetermination(action) {
    const url = `/v1/submissions/${action.id}/determinations/${action.determinationId}/`;
    try {
        yield put(Actions.showLoadingAction());
        yield call(
            apiFetch,
            {
                path: url,
                method: 'PUT',
                options: {
                    body: JSON.stringify(action.determinationData)
                }
            }
        );
        yield put(toggleDeterminationFormAction(false));
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }

}

export default function* homePageSaga() {
    yield takeLatest(ActionTypes.INITIALIZE, initialFetch);
    yield takeLatest(ActionTypes.SUBMIT_DETERMINATION_DATA, submitDetermination);
    yield takeLatest(ActionTypes.UPDATE_DETERMINATION_DATA, updateDetermination);
}
