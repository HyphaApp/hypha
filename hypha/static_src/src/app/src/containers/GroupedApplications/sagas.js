import {
    call,
    put,
    takeEvery
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import {apiFetch} from '@api/utils';

function* initialFetch(action) {

    try {
        yield put(Actions.showLoadingAction());
        let query = `?page_size=${action.searchParam.slice(4).split(',').length}&`;
        action.searchParam.slice(4).split(',').map(id => {
            return (
                query = query.concat(`id=${id}&`)
            );
        });
        const params = new URLSearchParams(query);
        const response = yield call(apiFetch, {path: '/v1/submissions/', params});
        const data = yield response.json();
        yield put(Actions.getApplicationsSuccessAction(data.results ? data.results : data));
        yield put(Actions.hideLoadingAction());
    }
    catch (e) {
        console.log('error', e);
        yield put(Actions.hideLoadingAction());
    }
}

export default function* groupedApplicationsSaga() {
    yield takeEvery(ActionTypes.INITIALIZE, initialFetch);
}
