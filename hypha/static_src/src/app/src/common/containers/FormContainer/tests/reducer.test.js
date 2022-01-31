import initialState, {formInitialState} from '../models';
import Reducer, {FormReducer} from '../reducer';
import * as Actions from '../actions';

describe('test reducer of determination form', () => {

    it('test  we get the initial data for undefined value of state', () => {
        expect(Reducer(undefined, {})).toEqual(initialState);
        expect(FormReducer(undefined, {})).toEqual({constraints: {}, errors: {}, readyToSubmit: false, values: {}});
    });

    it('on initialize form', () => {
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
            forms: formsInfo
        };
        const action = Actions.initializeFormAction('form1', {
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
        });
        expect(Reducer(initialState, action)).toEqual(state);
    });

    it('on add validation error', () => {
        const formsInfo = {
            form1: {
                constraints: {},
                errors: {
                    determination: 'this is an err msg'
                },
                readyToSubmit: false,
                values: {}
            }
        };

        const state = {
            forms: formsInfo
        };
        const action = Actions.addValidationErrorAction('form1', 'determination', 'this is an err msg');
        expect(Reducer(initialState, action)).toEqual(state);
    });

    it('on add validation error without error message', () => {
        const formsInfo = {
            form1: {
                constraints: {},
                errors: {
                },
                readyToSubmit: false,
                values: {}
            }
        };

        const state = {
            forms: formsInfo
        };
        const action = Actions.addValidationErrorAction('form1', 'determination', null);
        expect(Reducer(initialState, action)).toEqual(state);
    });

    it('on clear validation error', () => {
        const formsInfo = {
            form1: {
                constraints: {},
                errors: {},
                readyToSubmit: false,
                values: {}
            }
        };

        const state = {
            forms: formsInfo
        };
        const action = Actions.clearValidationErrorAction('form1');
        expect(Reducer(initialState, action)).toEqual(state);
    });

    it('on validate & submit form', () => {
        const formsInfo = {
            form1: {
                constraints: {},
                errors: {},
                readyToSubmit: true,
                values: {}
            }
        };

        const state = {
            forms: formsInfo
        };
        const action = Actions.validateAndSubmitFormAction('form1');
        expect(Reducer(initialState, action)).toEqual(state);
    });

    it('on update field value', () => {
        const formsInfo = {
            form1: {
                constraints: {},
                errors: {},
                readyToSubmit: false,
                values: {
                    message: '<p>message text</p>'
                }
            }
        };

        const state = {
            forms: formsInfo
        };
        const action = Actions.updateFieldValueAction('form1', 'message', '<p>message text</p>');
        expect(Reducer(initialState, action)).toEqual(state);
    });

});

