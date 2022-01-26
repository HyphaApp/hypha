import * as actions from '../actions';
import * as ActionTypes from '../constants';
import Reducer from '../reducer';

describe('Test actions of Determination form', () => {

    it('Should return the intialize action type', () => {
        const id = 1;
        const determinationId = 2;
        const expectedResult = {
            type: ActionTypes.INITIALIZE,
            id,
            determinationId
        };
        const action = actions.initializeAction(id, determinationId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the intialize action type without passing determination id', () => {
        const id = 1;
        const expectedResult = {
            type: ActionTypes.INITIALIZE,
            id,
            determinationId: null
        };
        const action = actions.initializeAction(id);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the determination fields success action type', () => {
        const data = Reducer(undefined, {}).metaStructure;
        const expectedResult = {
            type: ActionTypes.GET_DETERMINATION_FIELDS_SUCCESS,
            data
        };
        const action = actions.getDeterminationFieldsSuccessAction(data);
        expect(action).toEqual(expectedResult);
    });
    it('Should return the determination values success action type', () => {
        const data = Reducer(undefined, {}).initialValues;
        const expectedResult = {
            type: ActionTypes.GET_DETERMINATION_VALUES_SUCCESS,
            data
        };
        const action = actions.getDeterminationValuesSuccessAction(data);
        expect(action).toEqual(expectedResult);
    });
    it('Should return the submit determination action type', () => {
        const determinationData = {is_draft: true};
        const id = 1;
        const expectedResult = {
            type: ActionTypes.SUBMIT_DETERMINATION_DATA,
            id,
            determinationData
        };
        const action = actions.submitDeterminationAction(determinationData, id);
        expect(action).toEqual(expectedResult);
    });
    it('Should return the update determination action type', () => {
        const determinationData = {is_draft: true};
        const id = 1;
        const determinationId = 2;
        const expectedResult = {
            type: ActionTypes.UPDATE_DETERMINATION_DATA,
            id,
            determinationData,
            determinationId
        };
        const action = actions.updateDeterminationAction(determinationData, id, determinationId);
        expect(action).toEqual(expectedResult);
    });
    it('Should return the delete determination action type', () => {
        const id = 1;
        const determinationId = 2;
        const expectedResult = {
            type: ActionTypes.DELETE_DETERMINATION_DATA,
            id,
            determinationId
        };
        const action = actions.deleteDeterminationAction(determinationId, id);
        expect(action).toEqual(expectedResult);
    });
    it('Should return the show loading action type', () => {
        const expectedResult = {
            type: ActionTypes.SHOW_LOADING
        };
        const action = actions.showLoadingAction();
        expect(action).toEqual(expectedResult);
    });
    it('Should return the hide loading action type', () => {
        const expectedResult = {
            type: ActionTypes.HIDE_LOADING
        };
        const action = actions.hideLoadingAction();
        expect(action).toEqual(expectedResult);
    });
    it('Should return the clear initial values action type', () => {
        const expectedResult = {
            type: ActionTypes.CLEAR_INITIAL_VALUES
        };
        const action = actions.clearInitialValues();
        expect(action).toEqual(expectedResult);
    });
    it('Should return the toggle save draft action type', () => {
        const status = Reducer(undefined, {}).saveAsDraft;
        const expectedResult = {
            type: ActionTypes.TOGGLE_SAVE_DRAFT,
            status
        };
        const action = actions.toggleSaveDraftAction(status);
        expect(action).toEqual(expectedResult);
    });
});
