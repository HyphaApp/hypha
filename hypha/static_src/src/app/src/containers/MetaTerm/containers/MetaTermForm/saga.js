import {
    call,
    put,
    takeLatest,
  } from 'redux-saga/effects';
  import * as ActionTypes from './constants';
  import * as Actions from './actions';
  // import { updateSubmissionMetaTerms } from '@actions/submissions'
  import { apiFetch } from '@api/utils'
  
  export function* initialFetch() {
    
    try {
      yield put(Actions.showLoadingAction())
      // let response = yield call(apiFetch, {path : `/v1/meta_terms/`});
      // let data = yield response.json()
      let data = [
        { 
          "id": "21",
          "name": "Parent 1",
          "children": [
           { 
             "id":"6",
              "name": "Child 1",
              "children": [
                { 
                  "id":"18",
                  "children": [],
                  "name": "Grandchild 1"
                },
                {
                  "id":"9",
                  "children": [],
                  "name": "Grandchild 2"
                }
              ]
            },
            {
              "id":"7",
              "children": [{ 
                "id":"10",
                "children": [],
                "name": "Grandchild 3"
              }],
             "name": "Child 2"
            } 
          ]
        },
        {
        "id":"2",
         "name": "Parent 2",
         "children": []
        },
        {
          "id":"13",
         "name": "Parent 3",
         "children": []

        },
        {
          "id":"4",
         "name": "Parent 4",
         "children": [
           {
             "id": "20",
             "name": "child 3",
             "children": []
           }
         ]

        },
        {
          "id":"5",
          "name": "Parent 5",
          "children": []
        }
      ]
      yield put(
        Actions.getMetaTermsSuccessAction(data),
      );
      yield put(Actions.hideLoadingAction())
  
    } catch (e) {
      yield put(Actions.hideLoadingAction())
    }
  }
  
  export function* updateMetaTerms(action){
    const url = `/v1/submissions/${action.submissionId}/meta_terms/`
    try{
      yield put(Actions.showLoadingAction())
      yield call(
        apiFetch, 
        {
          path : url,
          method : "POST",
          options : {
              body : JSON.stringify(action.data),
          }
        }
        )
        let response = yield call(apiFetch, {path : `/v1/submissions/${action.submissionId}`});
        let data = yield response.json()
        yield put(updateSubmissionMetaTerms(action.submissionId, data.metaTerms))
      yield put(Actions.hideLoadingAction())
  }
    catch(e){
       yield put(Actions.hideLoadingAction())
    }
  
  }
  
  export default function* metaTermFormSaga() {
    yield takeLatest(ActionTypes.INITIALIZE, initialFetch);
    // yield takeLatest(ActionTypes.UPDATE_META_TERMS, updateMetaTerms)
  }
  