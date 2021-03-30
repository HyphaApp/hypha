import {
  call,
  put,
  takeEvery,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils';


export function* initialize(action) {
  try {
    if(action.submissionID){
      yield put(Actions.showLoadingAction(action.flagType))
      let response = yield call(apiFetch, {path : action.APIPath});
      let data = yield response.json()
      yield put(Actions.getSelectedFlagAction(action.flagType, data.result))
      yield put(Actions.hideLoadingAction(action.flagType))
    }
  } catch (e) {
    console.log("error", e)
    yield put(Actions.hideLoadingAction())
  }
}

export function* setFlag(action){
  try{
    yield put(Actions.setFlagClicked(action.flagType, true))
    yield call(apiFetch,
    {
    path : action.APIPath,
    method : "POST",
  })
  yield put(Actions.setFlagClicked(action.flagType, false))
  }catch(e){
    console.log("error", e)
    yield put(Actions.setFlagClicked(action.flagType, false))
  }
}


export default function* homePageSaga() {
  yield takeEvery(ActionTypes.INIT, initialize);
  yield takeEvery(ActionTypes.SET_FLAG, setFlag);
}
