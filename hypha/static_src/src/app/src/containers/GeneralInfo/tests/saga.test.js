import * as Actions from '../actions';
import {takeLatest, put, call} from 'redux-saga/effects';
import * as Sagas from '../sagas';
import {apiFetch} from '@api/utils';
import homePageSaga from '../sagas';
import * as ActionTypes from '../constants';


describe('Test userFetch  fn in SubmissionFilters module', () => {

    it('Should tirgger correct action for SUCCESS status', () => {

        const action = Actions.initializeAction();
        const generator = Sagas.userFetch(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next().value).toEqual(call(
            apiFetch,
            {
                path: '/v1/user/'
            }
        )
        );
        const data = {id: 2};
        expect(generator.next({json: () => data}).value).toEqual(data);
        expect(
            generator.next(data).value
        ).toEqual(
            put(Actions.getUserSuccessAction(data))
        );
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });



    it('Should tirgger correct action incase of error', () => {

        const action = Actions.initializeAction();
        const generator = Sagas.userFetch(action);
        generator.next();

        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );

        expect(generator.next().done).toBeTruthy();
    });

});

describe('Test takeLatest in General info module', () => {

    const genObject = homePageSaga();

    it('should wait for every INITIALIZE action and call userFetch', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.INITIALIZE,
                Sagas.userFetch));
    });

});
