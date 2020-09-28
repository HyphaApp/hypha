import {
  call,
  put,
  takeLatest,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils'

function* userFetch() {
  
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(apiFetch, {path : `/v1/user/`});
    let data = yield response.json()
    yield put(
      Actions.getUserSuccessAction(data),
    );
    yield put(Actions.hideLoadingAction())

  } catch (e) {
    yield put(Actions.hideLoadingAction())
  }
}

export default function* homePageSaga() {
  yield takeLatest(ActionTypes.INITIALIZE, userFetch);
}
