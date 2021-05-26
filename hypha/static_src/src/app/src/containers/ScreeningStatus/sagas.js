import {
  call,
  put,
  delay,
  takeEvery
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils';
import * as Selectors from './selectors';
import {select} from 'redux-saga/effects';


export function* setDefaultValue(action){
  try{
    if(!action.id)  return false;

    yield put(Actions.showLoadingAction())
    const response = yield call(apiFetch,
    {
    path : `/v1/submissions/${action.id}/screening_statuses/default/`,
    method : "POST",
    options : {
        body : JSON.stringify(action.data),
    }
  })
  const data = yield response.json()
  yield put(Actions.setDefaultSelectedAction(data))
  yield put(Actions.setVisibleSelectedAction([]))
  yield put(Actions.hideLoadingAction())

  }catch(e){
    yield put(Actions.hideLoadingAction())

  }
}

export function* setVisibleOption(action){
  try{
    if(!action.id)  return false;
    yield delay(300);
    yield put(Actions.showLoadingAction())
    const screening = yield select(Selectors.selectScreeningInfo)
    if(screening.selectedValues.some((value) => value.id == action.data.id)){
      yield call(apiFetch,
        {
        path : `/v1/submissions/${action.id}/screening_statuses/${action.data.id}`,
        method : "DELETE"
      })
      yield put(Actions.setVisibleSelectedAction(screening.selectedValues.filter((value) => value.id != action.data.id)))
    }
    else{
      let updatedData = {...action.data}
      delete updatedData.selected
      const response = yield call(apiFetch,
      {
      path : `/v1/submissions/${action.id}/screening_statuses/`,
        method : "POST",
        options : {
          body : JSON.stringify(updatedData),
      }
    })
    const data = yield response.json()
    yield put(Actions.setVisibleSelectedAction(data.filter(d => !d.default)))
  }
    yield put(Actions.hideLoadingAction())
  }catch(e){
    yield put(Actions.hideLoadingAction())
  }
}

export default function* homePageSaga() {
  yield takeEvery(ActionTypes.SELECT_DEFAULT_VALUE, setDefaultValue)
  yield takeEvery(ActionTypes.SELECT_VISIBLE_OPTION, setVisibleOption)
}
