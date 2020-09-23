import * as Immutable from 'seamless-immutable';

export const formInitialState = Immutable.from({
    values: {},
    errors: {},
    constraints: {},
    readyToSubmit: false
});

const initialState = Immutable.from({
    forms: {}
});

export default initialState;
