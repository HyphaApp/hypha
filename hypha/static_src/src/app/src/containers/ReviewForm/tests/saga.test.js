import * as Actions from '../actions';
import {takeLatest, put, call} from 'redux-saga/effects';
import * as Sagas from '../sagas';
import {apiFetch} from '@api/utils';
import * as ActionTypes from '../constants';
import homePageSaga from '../sagas';
import {toggleReviewFormAction, clearCurrentReviewAction} from '../../../redux/actions/submissions';

describe('Test the submit saga ', () => {

    it('test the submission of saga data', () => {
        const data = {
            reviewData: 'hi1',
            id: 2
        };
        const action = Actions.submitReviewAction(data.reviewData, data.id);
        const generator = Sagas.submitReview(action);
        expect(generator.next().value).toEqual(put(Actions.showLoadingAction()));
        expect(generator.next(`/v1/submissions/${data.id}/reviews/`).value).toEqual(call(
            apiFetch,
            {
                path: `/v1/submissions/${data.id}/reviews/`,
                method: 'POST',
                options: {
                    body: JSON.stringify(data.reviewData)
                }
            }
        )
        );
        expect(generator.next(false).value).toEqual(put(toggleReviewFormAction(false)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });

    it('test it produces an error', () => {
        const data = {
            reviewData: 'hi1',
            id: 2
        };
        const action = Actions.submitReviewAction(data.reviewData, data.id);
        const generator = Sagas.submitReview(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });
});

describe('Test the delete saga ', () => {

    it('test the deletion of saga data', () => {
        const data = {
            reviewId: 1,
            id: 2
        };
        const action = Actions.deleteReviewAction(data.reviewId, data.id);
        const generator = Sagas.deleteReview(action);
        expect(generator.next().value).toEqual(put(Actions.showLoadingAction()));
        expect(generator.next(`/v1/submissions/${data.id}/reviews/${data.reviewId}`).value).toEqual(call(
            apiFetch,
            {
                path: `/v1/submissions/${data.id}/reviews/${data.reviewId}`,
                method: 'DELETE'
            }
        )
        );
        expect(generator.next().value).toEqual(put(Actions.clearInitialValues()));
        expect(generator.next().value).toEqual(put(clearCurrentReviewAction()));
        expect(generator.next(false).value).toEqual(put(toggleReviewFormAction(false)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });

    it('test it produces an error', () => {
        const data = {
            reviewId: 1,
            id: 2
        };
        const action = Actions.deleteReviewAction(data.reviewId, data.id);
        const generator = Sagas.deleteReview(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });
});

describe('Test the update saga ', () => {

    it('test the submission of saga data', () => {
        const data = {
            reviewData: 'hi1',
            id: 2,
            reviewId: 1
        };
        const action = Actions.updateReviewAction(data.reviewData, data.id, data.reviewId);
        const generator = Sagas.updateReview(action);
        expect(generator.next().value).toEqual(put(Actions.showLoadingAction()));
        expect(generator.next(`/v1/submissions/${action.id}/reviews/${action.reviewId}/`).value).toEqual(call(
            apiFetch,
            {
                path: `/v1/submissions/${data.id}/reviews/${data.reviewId}/`,
                method: 'PUT',
                options: {
                    body: JSON.stringify(data.reviewData)
                }
            }
        )
        );
        expect(generator.next(false).value).toEqual(put(toggleReviewFormAction(false)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });

    it('test it produces an error', () => {
        const data = {
            reviewData: 'hi1',
            id: 2,
            reviewId: 1
        };
        const action = Actions.updateReviewAction(data.reviewData, data.id, data.reviewId);
        const generator = Sagas.updateReview(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });
});

describe('Test initial fetch in review form module', () => {

    it('Should trigger correct action for SUCCESS status', () => {
        const id = 1;
        const reviewId = 2;
        const action = Actions.initializeAction(id, reviewId);
        const generator = Sagas.initialFetch(action);

        expect(
            generator.next().value
        ).toEqual(
            put(Actions.showLoadingAction())
        );

        expect(generator.next().value).toEqual(call(
            apiFetch,
            {path: `/v1/submissions/${id}/reviews/fields/`}
        )
        );
        const data1 = {id: 1};
        expect(generator.next({json: () => data1}).value).toEqual(data1);
        expect(
            generator.next(data1).value
        ).toEqual(
            put(Actions.getReviewFieldsSuccessAction(data1))
        );
        expect(generator.next(`/v1/submissions/${action.id}/reviews/${action.reviewId}`).value)
            .toEqual(call(
                apiFetch,
                {path: `/v1/submissions/${id}/reviews/${reviewId}`}
            )
            );
        const data2 = {is_draft: true};
        expect(generator.next({json: () => data2}).value).toEqual(data2);
        expect(
            generator.next(data2).value
        ).toEqual(
            put(Actions.toggleSaveDraftAction(data2.is_draft))
        );
        expect(generator.next(data2).value).toEqual(put(Actions.getReviewValuesSuccessAction(data2)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });

    it('Should trigger correct action for SUCCESS status with review id null', () => {
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
            {path: `/v1/submissions/${id}/reviews/fields/`}
        )
        );
        const data1 = {id: 1};
        expect(generator.next({json: () => data1}).value).toEqual(data1);
        expect(
            generator.next(data1).value
        ).toEqual(
            put(Actions.getReviewFieldsSuccessAction(data1))
        );
        expect(generator.next(`/v1/submissions/${action.id}/reviews/draft/`).value)
            .toEqual(call(
                apiFetch,
                {path: `/v1/submissions/${id}/reviews/draft/`}
            )
            );
        const data2 = null;
        expect(generator.next({json: () => data2}).value).toEqual(data2);
        expect(generator.next(data2).value).toEqual(put(Actions.getReviewValuesSuccessAction(data2)));
        expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()));
        expect(generator.next().done).toBeTruthy();
    });


    it('Should tirgger correct action incase of error', () => {
        const id = 1;
        const reviewId = 2;
        const action = Actions.initializeAction(id, reviewId);
        const generator = Sagas.initialFetch(action);
        generator.next();
        expect(generator.throw(new Error()).value).toEqual(
            put(Actions.hideLoadingAction())
        );
        expect(generator.next().done).toBeTruthy();
    });
});

describe('Test takeLatest in Review form module', () => {

    const genObject = homePageSaga();

    it('should wait for every INITIALIZE action and call initialFetch', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.INITIALIZE,
                Sagas.initialFetch));
    });

    it('should wait for every SUBMIT_REVIEW_DATA action and call submitReview', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.SUBMIT_REVIEW_DATA,
                Sagas.submitReview));
    });

    it('should wait for every DELETE_REVIEW_DATA action and call deleteReview', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.DELETE_REVIEW_DATA,
                Sagas.deleteReview));
    });

    it('should wait for every UPDATE_REVIEW_DATA action and call updateReview', () => {
        expect(genObject.next().value)
            .toEqual(takeLatest(ActionTypes.UPDATE_REVIEW_DATA,
                Sagas.updateReview));
    });
});
