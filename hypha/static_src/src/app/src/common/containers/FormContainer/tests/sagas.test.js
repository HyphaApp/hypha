import * as Actions from '../actions';
import {put, call, select, takeEvery} from 'redux-saga/effects';
import * as Sagas from '../sagas';
import {apiFetch} from '@api/utils';
import * as Selectors from '../selectors';
import * as ActionTypes from '../constants';
import formContainerSaga from '../sagas';

describe('Test sagas in form container module', () => {

    it('Check validate fields saga', () => {

        const formsInfo = {
            form1: {
                values: {
                    determination: '0',
                    message: '<p>asdasda</p>'
                },
                constraints: {
                    determination: {
                        presence: {
                            allowEmpty: false
                        }
                    }
                }
            }
        };
        const state = {
            FormContainer: {
                forms: formsInfo
            }
        };
        const formId = 'form1';
        const action = Actions.validateAndSubmitFormAction(formId);
        const generator = Sagas.validateFields(action);
        expect(
            generator.next().value
        ).toEqual(
            select(Selectors.selectFormsInfo)
        );

        expect(
            generator.next(formsInfo).value
        ).toEqual(
            put(Actions.clearValidationErrorAction(formId))
        );
        expect(generator.next().done).toBeTruthy();
    });

    it('Check validate fields saga produce an error', () => {

        const formsInfo = {
            form1: {
                values: {
                    determination: '',
                    message: '<p>asdasda</p>'
                },
                constraints: {
                    determination: {
                        presence: {
                            allowEmpty: false
                        }
                    }
                }
            }
        };
        const state = {
            FormContainer: {
                forms: formsInfo
            }
        };
        const formId = 'form1';
        const action = Actions.validateAndSubmitFormAction(formId);
        const generator = Sagas.validateFields(action);
        expect(
            generator.next().value
        ).toEqual(
            select(Selectors.selectFormsInfo)
        );

        expect(
            generator.next(formsInfo).value
        ).toEqual(
            put(Actions.clearValidationErrorAction(formId))
        );

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.addValidationErrorAction(formId, 'determination', "Determination can't be blank"))
        );

        expect(generator.next().done).toBeTruthy();
    });

    it('Check validateField saga', () => {

        const formsInfo = {
            form1: {
                values: {
                    determination: '0',
                    message: '<p>asdasda</p>'
                },
                constraints: {
                    determination: {
                        presence: {
                            allowEmpty: false
                        }
                    }
                }
            }
        };
        const state = {
            FormContainer: {
                forms: formsInfo
            }
        };
        const formId = 'form1';
        const action = Actions.updateFieldValueAction(formId, 'determination', '0');
        const generator = Sagas.validateField(action);
        expect(
            generator.next().value
        ).toEqual(
            select(Selectors.selectFormsInfo)
        );

        expect(
            generator.next(formsInfo).value
        ).toEqual(
            put(Actions.addValidationErrorAction(formId, 'determination', false))
        );

        expect(generator.next().done).toBeTruthy();
    });

    it('Check validateField saga produce an error', () => {

        const formsInfo = {
            form1: {
                values: {
                    determination: '',
                    message: '<p>asdasda</p>'
                },
                constraints: {
                    determination: {
                        presence: {
                            allowEmpty: false
                        }
                    }
                }
            }
        };
        const state = {
            FormContainer: {
                forms: formsInfo
            }
        };
        const formId = 'form1';
        const action = Actions.updateFieldValueAction(formId, 'determination', '');
        const generator = Sagas.validateField(action);
        expect(
            generator.next().value
        ).toEqual(
            select(Selectors.selectFormsInfo)
        );

        expect(
            generator.next(formsInfo).value
        ).toEqual(
            put(Actions.addValidationErrorAction(formId, 'determination', "Determination can't be blank"))
        );

        expect(generator.next().done).toBeTruthy();
    });


    const genObject = formContainerSaga();

    it('should wait for every UPDATE_FIELD_VALUE action and call validateField', () => {
        expect(genObject.next().value)
            .toEqual(takeEvery(ActionTypes.UPDATE_FIELD_VALUE,
                Sagas.validateField));
    });

    it('should wait for every VALIDATE_AND_SUBMIT_FORM action and call validateFields', () => {
        expect(genObject.next().value)
            .toEqual(takeEvery(ActionTypes.VALIDATE_AND_SUBMIT_FORM,
                Sagas.validateFields));
    });
});
