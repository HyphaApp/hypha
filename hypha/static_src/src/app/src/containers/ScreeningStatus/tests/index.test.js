import React from "react";
import {mount} from "enzyme";
import {Provider} from "react-redux";
import configureMockStore from "redux-mock-store";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import initialState from '../models'
import  {ScreeningStatusContainer}  from '../index.js';
import LoadingPanel from '@components/LoadingPanel'

enzyme.configure({adapter: new Adapter()});

const mockStore = configureMockStore();
describe("Test screening status Container", () => {
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
                <ScreeningStatusContainer screeningInfo={{loading : true}} initializeAction={initializeAction} submissionID={1}/>
            </Provider>
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(0)
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });
});
