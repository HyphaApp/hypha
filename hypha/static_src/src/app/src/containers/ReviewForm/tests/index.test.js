import React from "react";
import {mount} from "enzyme";
import {Provider} from "react-redux";
import configureMockStore from "redux-mock-store";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import initialState from '../models'
import  {ReviewFormContainer}  from '../index.js';
import LoadingPanel from '@components/LoadingPanel'

enzyme.configure({adapter: new Adapter()});

const mockStore = configureMockStore();
describe("Test Review form Container", () => {
    let store;
    const locale = "en-US";
    it("Should render review form without issues", () => {
        store = mockStore({
            "Settings": initialState
        });
        const initializeAction = jest.fn()
        const wrapper = mount(
            <Provider
                store={store}
            >
                <ReviewFormContainer formData={{loading : true}} initializeAction={initializeAction}/>
            </Provider>
        );
        expect(wrapper.find('.container').length).toEqual(1)
        expect(wrapper.find('h3').text()).toBe("Create Review")
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });
});
