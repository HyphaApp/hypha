import * as Actions from '../actions';
import {put, call, takeLatest} from 'redux-saga/effects';
import * as Sagas from '../sagas';
import {apiFetch} from '@api/utils';
import {toggleDeterminationFormAction} from '../../../redux/actions/submissions';
import homePageSaga from '../sagas';
import * as ActionTypes from '../constants';


describe('Test submit Determination in Determination form module', () => {

    it('Should trigger correct action for SUCCESS status', () => {
        const determinationData = 'data';
        const id = 1;
        const action = Actions.submitDeterminationAction(determinationData, id);
        const generator = Sagas.submitDetermination(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next(`/v1/submissions/${action.id}/determinations/`).value).toEqual(call(
            apiFetch,
            {
                path: `/v1/submissions/${id}/determinations/`,
                method: 'POST',
                options: {
                    body: JSON.stringify(determinationData)
                }
            }
        )
        );
        expect(
            generator.next(false).value
        ).toEqual(
            put(toggleDeterminationFormAction(false))
        );
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });


    it('Should tirgger correct action incase of error', () => {
        const determinationData = 'data';
        const id = 1;
        const action = Actions.submitDeterminationAction(determinationData, id);
        const generator = Sagas.submitDetermination(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });

});

describe('Test update Determination in Determination form module', () => {

    it('Should trigger correct action for SUCCESS status', () => {
        const determinationData = 'data';
        const id = 1;
        const determinationId = 2;
        const action = Actions.updateDeterminationAction(determinationData, id, determinationId);
        const generator = Sagas.updateDetermination(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next(`/v1/submissions/${action.id}/determinations/${action.determinationId}/`).value).toEqual(call(
            apiFetch,
            {
                path: `/v1/submissions/${id}/determinations/${determinationId}/`,
                method: 'PUT',
                options: {
                    body: JSON.stringify(determinationData)
                }
            }
        )
        );
        expect(
            generator.next(false).value
        ).toEqual(
            put(toggleDeterminationFormAction(false))
        );
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });


    it('Should tirgger correct action incase of error', () => {
        const determinationData = 'data';
        const id = 1;
        const determinationId = 2;
        const action = Actions.updateDeterminationAction(determinationData, id, determinationId);
        const generator = Sagas.updateDetermination(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });

});

describe('Test initial fetch in Determination form module', () => {

    it('Should trigger correct action for SUCCESS status', () => {
        const id = 1;
        const determinationId = 2;
        const action = Actions.initializeAction(id, determinationId);
        const generator = Sagas.initialFetch(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next().value).toEqual(call(
            apiFetch,
            {path: `/v1/submissions/${action.id}/determinations/fields/`}
        )
        );
        const data1 = {id: 1};
        expect(generator.next({json: () => data1}).value).toEqual(data1);
        expect(
            generator.next(data1).value
        ).toEqual(
            put(Actions.getDeterminationFieldsSuccessAction(data1))
        );
        expect(generator.next(`/v1/submissions/${action.id}/determinations/${action.determinationId}`).value)
            .toEqual(call(
                apiFetch,
                {path: `/v1/submissions/${id}/determinations/${determinationId}`}
            )
            );
        const data2 = {is_draft: true};
        expect(generator.next({json: () => data2}).value).toEqual(data2);
        expect(
            generator.next(data2).value
        ).toEqual(
            put(Actions.toggleSaveDraftAction(data2.is_draft))
        );
        expect(generator.next(data2).value).toEqual(put(Actions.getDeterminationValuesSuccessAction(data2)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });

    it('Should trigger correct action for SUCCESS status with determination id as null', () => {
        const id = 1;
        const action = Actions.initializeAction(id);
        const generator = Sagas.initialFetch(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next().value).toEqual(call(
            apiFetch,
            {path: `/v1/submissions/${action.id}/determinations/fields/`}
        )
        );
        const data1 = {id: 1};
        expect(generator.next({json: () => data1}).value).toEqual(data1);
        expect(
            generator.next(data1).value
        ).toEqual(
            put(Actions.getDeterminationFieldsSuccessAction(data1))
        );
        expect(generator.next(`/v1/submissions/${action.id}/determinations/draft/`).value)
            .toEqual(call(
                apiFetch,
                {path: `/v1/submissions/${id}/determinations/draft/`}
            )
            );
        const data2 = null;
        expect(generator.next({json: () => data2}).value).toEqual(data2);
        expect(generator.next(data2).value).toEqual(put(Actions.getDeterminationValuesSuccessAction(data2)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });


    it('Should tirgger correct action incase of error', () => {
        const id = 1;
        const determinationId = 2;
        const action = Actions.initializeAction(id, determinationId);
        const generator = Sagas.initialFetch(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });

});

describe('Test takeLatest in Determination form module', () => {

    const genObject = homePageSaga();

    it('should wait for every INITIALIZE action and call initialFetch', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.INITIALIZE,
                Sagas.initialFetch));
    });

    it('should wait for every SUBMIT_DETERMINATION_DATA action and call submitDetermination', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.SUBMIT_DETERMINATION_DATA,
                Sagas.submitDetermination));
    });

    it('should wait for every UPDATE_DETERMINATION_DATA action and call updateDetermination', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.UPDATE_DETERMINATION_DATA,
                Sagas.updateDetermination));
    });
});
