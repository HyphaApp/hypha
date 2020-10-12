import {
  call,
  put,
  takeLatest,
} from 'redux-saga/effects';
import * as ActionTypes from './constants';
import * as Actions from './actions';
import { toggleReviewFormAction, clearCurrentReviewAction } from '../../redux/actions/submissions'
import { apiFetch } from '@api/utils'

function* initialFetch(action) {
  
  try {
    yield put(Actions.showLoadingAction())
    let response = yield call(apiFetch, {path : `/v1/submissions/${action.id}/reviews/fields/`});
    let data = yield response.json()
    yield put(
      Actions.getReviewFieldsSuccessAction(data),
    );
   let url = `/v1/submissions/${action.id}/reviews/draft/`

    if(action.reviewId !== null){
       url = `/v1/submissions/${action.id}/reviews/${action.reviewId}`
       }

       response = yield call(apiFetch, {path : url})
       data = yield response.json()
       if(data)
       {
       yield put(Actions.toggleSaveDraftAction(data.is_draft))
     }
       yield put(Actions.getReviewValuesSuccessAction(data))
        yield put(Actions.hideLoadingAction())

  } catch (e) {
    yield put(Actions.hideLoadingAction())
  }
}

function* submitReview(action){
  const url = `/v1/submissions/${action.id}/reviews/`
  try{
    yield put(Actions.showLoadingAction())
    yield call(
      apiFetch, 
      {
        path : url,
        method : "POST",
        options : {
            body : JSON.stringify(action.reviewData),
        }
      }
      )
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())
  }catch(e){
     yield put(Actions.hideLoadingAction())
  }
}

function* deleteReview(action){
  const url = `/v1/submissions/${action.id}/reviews/${action.reviewId}`
  try{
    yield put(Actions.showLoadingAction())
    yield call(
      apiFetch, 
      {
        path : url,
        method : "DELETE",
      }
      )
    yield put(Actions.clearInitialValues())
    yield put(clearCurrentReviewAction()) 
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())

  }catch(e){
     yield put(Actions.hideLoadingAction())
  }
}

function* updateReview(action){
  const url = `/v1/submissions/${action.id}/reviews/${action.reviewId}/`
  try{
    yield put(Actions.showLoadingAction())
    yield call(
      apiFetch, 
      {
        path : url,
        method : "PUT",
        options : {
            body : JSON.stringify(action.reviewData),
        }
      }
      )
    yield put(toggleReviewFormAction(false))
    yield put(Actions.hideLoadingAction())
}
  catch(e){
     yield put(Actions.hideLoadingAction())
  }

}

export default function* homePageSaga() {
  yield takeLatest(ActionTypes.INITIALIZE, initialFetch);
  yield takeLatest(ActionTypes.SUBMIT_REVIEW_DATA, submitReview)
  yield takeLatest(ActionTypes.DELETE_REVIEW_DATA, deleteReview)
  yield takeLatest(ActionTypes.UPDATE_REVIEW_DATA, updateReview)
}
