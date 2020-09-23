import { takeEvery, put, select } from 'redux-saga/effects';
// eslint-disable-next-line no-unused-vars
import regeneratorRuntime from "regenerator-runtime";

import * as ActionTypes from "./constants";
import * as Actions from "./actions";
import * as Selectors from "./selectors";
import Validator from "./Validator";

export function* validateFields(action){
    const formsInfo = yield select(Selectors.selectFormsInfo);
    const formId = action.formId;
    const validator = new Validator(formsInfo[formId].values, formsInfo[formId].constraints);
    const errors = validator.validate();

    yield put(Actions.clearValidationErrorAction(formId));
    if(errors) {
        for(const field_name in errors){
            yield put(Actions.addValidationErrorAction(formId, field_name, errors[field_name][0] ))
        }
    }
}


export function* validateField(action) {
    const formsInfo = yield select(Selectors.selectFormsInfo);
    const formId = action.formId;
    const validator = new Validator(formsInfo[formId].values, formsInfo[formId].constraints);
    const error = validator.validateSingle(action.fieldName);
    yield put(Actions.addValidationErrorAction(
        formId, 
        action.fieldName,
        !error ? error : error[action.fieldName][0])
    )
}


export default function* formContainerSaga() {
  yield takeEvery(
    ActionTypes.UPDATE_FIELD_VALUE,
    validateField
  );
  yield takeEvery(
    ActionTypes.VALIDATE_AND_SUBMIT_FORM,
    validateFields
  );
}
