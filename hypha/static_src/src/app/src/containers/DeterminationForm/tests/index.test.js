import React from 'react';
import {mount} from 'enzyme';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import {DeterminationFormContainer} from '../index.js';
import LoadingPanel from '@components/LoadingPanel';
import FormContainer from '@common/containers/FormContainer';
enzyme.configure({adapter: new Adapter()});


describe('Test Determination Container', () => {
    it('Should render determination without issues', () => {
        const initializeAction = jest.fn();
        const wrapper = mount(
            <DeterminationFormContainer
                formData={{loading: true}}
                initializeAction={initializeAction}
                submissionID={1}/>
        );
        expect(wrapper.find('.determination-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Create Determination');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, null);
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render determination with loading false', () => {
        const initializeAction = jest.fn();
        const toggleDeterminationForm = jest.fn();
        const clearCurrentDetermination = jest.fn();
        const submitDetermination = jest.fn();
        const updateDetermination = jest.fn();
        const wrapper = shallow(
            <DeterminationFormContainer
                formData={{
                    loading: false,
                    saveAsDraft: true,
                    initialValues: [],
                    metaStructure: []}}
                initializeAction={initializeAction}
                submissionID={1}
                determinationId={2}
                toggleDeterminationForm={toggleDeterminationForm}
                clearCurrentDetermination={clearCurrentDetermination}
                submitDetermination={submitDetermination}
                updateDetermination={updateDetermination}
            />
        );
        expect(wrapper.find('.determination-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Update Determination');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, 2);
        expect(toggleDeterminationForm).not.toHaveBeenCalled();
        expect(clearCurrentDetermination).not.toHaveBeenCalled();
        expect(submitDetermination).not.toHaveBeenCalled();
        expect(updateDetermination).not.toHaveBeenCalled();
        expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render determination with loading false & currentDetermination exists', () => {
        const initializeAction = jest.fn();
        const toggleDeterminationForm = jest.fn();
        const clearCurrentDetermination = jest.fn();
        const submitDetermination = jest.fn();
        const updateDetermination = jest.fn();
        const wrapper = shallow(
            <DeterminationFormContainer
                formData={{
                    loading: false,
                    saveAsDraft: true,
                    initialValues: [],
                    metaStructure: [{type: 'type1'}, {type: 'TypedChoiceField'}]}}
                initializeAction={initializeAction}
                submissionID={1}
                determinationId={2}
                currentDetermination={3}
                toggleDeterminationForm={toggleDeterminationForm}
                clearCurrentDetermination={clearCurrentDetermination}
                submitDetermination={submitDetermination}
                updateDetermination={updateDetermination}
            />
        );
        expect(wrapper.find('.determination-form-container').length).toEqual(1);
        expect(wrapper.find('h3').text()).toBe('Update Determination');
        expect(initializeAction).toHaveBeenCalled();
        expect(initializeAction).toHaveBeenCalledWith(1, 2);
        expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });
});
