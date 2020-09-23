import {
  call,
  put,
  takeLatest,
} from 'redux-saga/effects';
// import { getNAV, mergeSeries } from 'utils/chart';
// import * as Actions from './actions';
import * as ActionTypes from './constants';
import axios from 'axios';
import * as Actions from './actions';
import { toggleReviewFormAction, clearCurrentReviewAction } from '../../redux/actions/submissions'
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

function* initialFetch(action) {
  
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(axios.get, `/api/v1/submissions/${action.id}/reviews/fields/`);
    
    yield put(
      Actions.getReviewFieldsSuccessAction(response.data),
    );
   let url = `/api/v1/submissions/${action.id}/reviews/draft/`

    if(action.reviewId !== null){
       url = `/api/v1/submissions/${action.id}/reviews/${action.reviewId}`
       }

       response = yield call(axios.get, url)
       if(response.data)
       {
       yield put(Actions.toggleSaveDraftAction(response.data.is_draft))
     }
       yield put(Actions.getReviewValuesSuccessAction(response.data))
        yield put(Actions.hideLoadingAction())

  } catch (e) {
    yield put(Actions.hideLoadingAction())
    console.log(e);
  }
}

function* submitReview(action){
  const url = `/api/v1/submissions/${action.id}/reviews/`
  try{
    yield put(Actions.showLoadingAction())
    yield call(axios.post, url, action.reviewData)
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())
  }catch(e){
     yield put(Actions.hideLoadingAction())
    console.log(e);
  }
}

function* deleteReview(action){
  const url = `/api/v1/submissions/${action.id}/reviews/${action.reviewId}`
  try{
    yield put(Actions.showLoadingAction())
    yield call(axios.delete, url)
    yield put(Actions.clearInitialValues())
    yield put(clearCurrentReviewAction()) 
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())

  }catch(e){
     yield put(Actions.hideLoadingAction())
    console.log(e);

  }
}

function* updateReview(action){
  const url = `/api/v1/submissions/${action.id}/reviews/${action.reviewId}/`
  try{
    yield put(Actions.showLoadingAction())
    yield call(axios.put, url, action.reviewData)
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())
}
  catch(e){
     yield put(Actions.hideLoadingAction())
    console.log(e);

  }

}

export default function* homePageSaga() {
  yield takeLatest(ActionTypes.INITIALIZE, initialFetch);
  yield takeLatest(ActionTypes.SUBMIT_REVIEW_DATA, submitReview)
  yield takeLatest(ActionTypes.DELETE_REVIEW_DATA, deleteReview)
  yield takeLatest(ActionTypes.UPDATE_REVIEW_DATA, updateReview)
}
