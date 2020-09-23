import {
  call,
  put,
  takeLatest,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import axios from 'axios';
import * as Actions from './actions';
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

function* userFetch() {
  
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(axios.get, `/api/v1/user/`);
    yield put(
      Actions.getUserSuccessAction(response.data),
    );
    yield put(Actions.hideLoadingAction())

  } catch (e) {
    yield put(Actions.hideLoadingAction())
    console.log(e);
  }
}

export default function* homePageSaga() {
  yield takeLatest(ActionTypes.INITIALIZE, userFetch);
}
