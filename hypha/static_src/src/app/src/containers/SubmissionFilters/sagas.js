import {
  call,
  put,
  takeEvery,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { apiFetch } from '@api/utils'


function getFilters(params) {
  let filters  = {}
  const filterKey = ["f_fund", "f_round", "f_status", "f_screening_statuses", "f_lead", "f_reviewers"]
  const urlParams = new URLSearchParams(params)
  for (const key of filterKey) {
    if(urlParams.get(key)){
      if(key == "f_status"){
        filters[key.slice(2)] = JSON.parse(urlParams.get(key))
      }else filters[key.slice(2)] = urlParams.get(key).split(",").map(i => i !== 'null' ? Number(i) : null)
    }
  }
  return filters
}

export function* initialFetch(action) {
  
  try {
    yield put(Actions.showLoadingAction())
    const response = yield call(apiFetch, {path : `/v1/submissions_filter/`});
    const data = yield response.json()
    yield put(Actions.getFiltersSuccessAction(data));
    if(action.searchParams){
      const filters = getFilters(action.searchParams)
      for (const filterKey in filters){
        yield put(Actions.updateSelectedFilterAction(filterKey, filters[filterKey]))
      }
      yield put(action.filterAction())
  }
    yield put(Actions.hideLoadingAction())
  } catch (e) {
    yield put(Actions.hideLoadingAction())
  }
}

export default function* homePageSaga() {
  yield takeEvery(ActionTypes.INITIALIZE, initialFetch);
}
