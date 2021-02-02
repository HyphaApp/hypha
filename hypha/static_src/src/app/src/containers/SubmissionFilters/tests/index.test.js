import React from "react";
import {mount} from "enzyme";
import {Provider} from "react-redux";
import configureMockStore from "redux-mock-store";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import initialState from '../models'
import  {SubmissionFiltersContainer}  from '../index.js';
import LoadingPanel from '@components/LoadingPanel'

enzyme.configure({adapter: new Adapter()});

const mockStore = configureMockStore();
describe("Test submission filter Container", () => {
    let store;
    const locale = "en-US";
    it("Should render submission filter without issues", () => {
        store = mockStore({
            "Settings": initialState
        });
        const initializeAction = jest.fn()
        const wrapper = mount(
            <Provider
                store={store}
            >
                <SubmissionFiltersContainer submissionFilters={{loading : true}} initializeAction={initializeAction}/>
            </Provider>
        );
        expect(wrapper.find('.filter-container').length).toEqual(0)
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });
});
