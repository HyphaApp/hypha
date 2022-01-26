import * as actions from '../actions';
import * as ActionTypes from '../constants';
import Reducer from '../reducer';

describe('Test actions of GeneralInfo', () => {
    it('should return the intialize action type', () => {
        const expectedResult = {
            type: ActionTypes.INITIALIZE
        };
        const action = actions.initializeAction();
        expect(action).toEqual(expectedResult);
    });
    it('should return the user success action type', () => {
        const data = Reducer(undefined, {}).user;
        const expectedResult = {
            type: ActionTypes.GET_USER_SUCCESS,
            data
        };
        const action = actions.getUserSuccessAction(data);
        expect(action).toEqual(expectedResult);
    });
    it('should return the show loading action type', () => {
        const expectedResult = {
            type: ActionTypes.SHOW_LOADING
        };
        const action = actions.showLoadingAction();
        expect(action).toEqual(expectedResult);
    });
    it('should return the hide loading action type', () => {
        const expectedResult = {
            type: ActionTypes.HIDE_LOADING
        };
        const action = actions.hideLoadingAction();
        expect(action).toEqual(expectedResult);
    });
});
