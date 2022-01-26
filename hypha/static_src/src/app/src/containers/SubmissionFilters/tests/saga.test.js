import * as Actions from '../actions';
import {takeEvery, put, call} from 'redux-saga/effects';
import * as Sagas from '../sagas';
import {apiFetch} from '@api/utils';
import {toggleReviewFormAction, clearCurrentReviewAction} from '../../../redux/actions/submissions';
import homePageSaga from '../sagas';
import * as ActionTypes from '../constants';

describe('Test initialFetch  fn in SubmissionFilters module', () => {

    it('Should tirgger correct action for SUCCESS status', () => {

        const action = Actions.initializeAction();
        const generator = Sagas.initialFetch(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next().value).toEqual(call(
            apiFetch,
            {
                path: '/v1/submissions_filter/'
            }
        )
        );
        const data = {id: 2};
        expect(generator.next({json: () => data}).value).toEqual(data);
        expect(
            generator.next(data).value
        ).toEqual(
            put(Actions.getFiltersSuccessAction(data))
        );
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });



    it('Should tirgger correct action incase of error', () => {

        const action = Actions.initializeAction();
        const generator = Sagas.initialFetch(action);
        generator.next();

        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );

        expect(generator.next().done).toBeTruthy();
    });

});

describe('Test takeEvery in Submission filters module', () => {

    const genObject = homePageSaga();

    it('should wait for every INITIALIZE action and call initialFetch', () => {
        expect(genObject.next().value)
            .toEqual(takeEvery(ActionTypes.INITIALIZE,
                Sagas.initialFetch));
    });
});
