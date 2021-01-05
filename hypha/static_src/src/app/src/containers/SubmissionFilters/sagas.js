import {
  call,
  put,
  takeEvery,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils'

function* initialFetch() {
  
  try {
    yield put(Actions.showLoadingAction())
    const response = yield call(apiFetch, {path : `/v1/submissions_filter/`});
    const data = yield response.json()
    yield put(Actions.getFiltersSuccessAction(data));
    yield put(Actions.hideLoadingAction())
  } catch (e) {
    console.log("error", e)
    yield put(Actions.hideLoadingAction())
  }
}

export default function* homePageSaga() {
  yield takeEvery(ActionTypes.INITIALIZE, initialFetch);
}
