import {
    call,
    put,
    takeLatest
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import {updateSubmissionMetaTerms} from '@actions/submissions';
import {apiFetch} from '@api/utils';
import {camelizeKeys} from 'humps';


export function* initialFetch() {

    try {
        yield put(Actions.showLoadingAction());
        let response = yield call(apiFetch, {path: '/v1/meta_terms/'});
        let data = yield response.json();
        yield put(
            Actions.getMetaTermsSuccessAction(data.results),
        );
        yield put(Actions.hideLoadingAction());

    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export function* updateMetaTerms(action) {
    const url = `/v1/submissions/${action.submissionId}/meta_terms/`;
    try {
        yield put(Actions.showLoadingAction());
        yield call(
            apiFetch,
            {
                path: url,
                method: 'POST',
                options: {
                    body: JSON.stringify({meta_terms: action.data})
                }
            }
        );
        let response = yield call(apiFetch, {path: `/v1/submissions/${action.submissionId}/`});
        response = yield response.json();
        const data = yield camelizeKeys(response);
        yield put(updateSubmissionMetaTerms(action.submissionId, data.metaTerms));
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        yield put(Actions.hideLoadingAction());
    }
}

export default function* metaTermFormSaga() {
    yield takeLatest(ActionTypes.INITIALIZE, initialFetch);
    yield takeLatest(ActionTypes.UPDATE_META_TERMS, updateMetaTerms);
}
