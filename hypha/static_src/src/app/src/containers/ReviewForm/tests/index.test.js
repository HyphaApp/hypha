import React from 'react';
import {mount} from 'enzyme';
import {Provider} from 'react-redux';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import initialState from '../models';
import {ReviewFormContainer} from '../index.js';
import LoadingPanel from '@components/LoadingPanel';
enzyme.configure({adapter: new Adapter()});
import FormContainer from '@common/containers/FormContainer';


describe('Test Review form Container', () => {
    it('Should render review form with loading true', () => {
        const initializeAction = jest.fn();
        const wrapper = mount(
            <ReviewFormContainer
                formData={{loading: true}}
                initializeAction={initializeAction}/>
        );
        expect(wrapper.find('.review-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Create Review');
        expect(initializeAction).toHaveBeenCalled();
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render review with loading false', () => {
        const initializeAction = jest.fn();
        const toggleReviewForm = jest.fn();
        const deleteReview = jest.fn();
        const submitReview = jest.fn();
        const updateReview = jest.fn();
        const wrapper = shallow(
            <ReviewFormContainer
                formData={{
                    loading: false,
                    saveAsDraft: true,
                    initialValues: [],
                    metaStructure: []}}
                initializeAction={initializeAction}
                submissionID={1}
                reviewId={2}
                toggleReviewForm={toggleReviewForm}
                deleteReview={deleteReview}
                submitReview={submitReview}
                updateReview={updateReview}
            />
        );
        expect(wrapper.find('.review-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Update Review');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, 2);
        expect(toggleReviewForm).not.toHaveBeenCalled();
        expect(deleteReview).not.toHaveBeenCalled();
        expect(submitReview).not.toHaveBeenCalled();
        expect(updateReview).not.toHaveBeenCalled();
        expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render review with loading false & saveAsDraft false', () => {
        const initializeAction = jest.fn();
        const toggleReviewForm = jest.fn();
        const deleteReview = jest.fn();
        const submitReview = jest.fn();
        const updateReview = jest.fn();
        const wrapper = shallow(
            <ReviewFormContainer
                formData={{
                    loading: false,
                    saveAsDraft: false,
                    initialValues: [],
                    metaStructure: [{type: 'type1'}, {type: 'TypedChoiceField'}]}}
                initializeAction={initializeAction}
                submissionID={1}
                currentDetermination={3}
                toggleReviewForm={toggleReviewForm}
                deleteReview={deleteReview}
                submitReview={submitReview}
                updateReview={updateReview}
            />
        );
        expect(wrapper.find('.review-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Create Review');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, null);
        expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render review with loading false & saveAsDraft false & review id exists', () => {
        const initializeAction = jest.fn();
        const toggleReviewForm = jest.fn();
        const deleteReview = jest.fn();
        const submitReview = jest.fn();
        const updateReview = jest.fn();
        const wrapper = shallow(
            <ReviewFormContainer
                formData={{
                    loading: false,
                    saveAsDraft: false,
                    initialValues: [],
                    metaStructure: []}}
                initializeAction={initializeAction}
                submissionID={1}
                reviewId={2}
                toggleReviewForm={toggleReviewForm}
                deleteReview={deleteReview}
                submitReview={submitReview}
                updateReview={updateReview}
            />
        );
        expect(wrapper.find('.review-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Update Review');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, 2);
        expect(toggleReviewForm).not.toHaveBeenCalled();
        expect(deleteReview).not.toHaveBeenCalled();
        expect(submitReview).not.toHaveBeenCalled();
        expect(updateReview).not.toHaveBeenCalled();
        expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });
});
