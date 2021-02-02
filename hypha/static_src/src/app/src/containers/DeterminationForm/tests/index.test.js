import React from "react";
import {mount} from "enzyme";
import {Provider} from "react-redux";
import configureMockStore from "redux-mock-store";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import initialState from '../models'
import  {DeterminationFormContainer}  from '../index.js';
import LoadingPanel from '@components/LoadingPanel';
import FormContainer from '@common/containers/FormContainer';


enzyme.configure({adapter: new Adapter()});

const mockStore = configureMockStore();
describe("Test Determination Container", () => {
    let store;
    const locale = "en-US";
    it("Should render determination without issues", () => {
        store = mockStore({
            "Settings": initialState
        });
        const initializeAction = jest.fn()
        const wrapper = mount(
            <Provider
                store={store}
            >
                <DeterminationFormContainer formData={{loading : true}} initializeAction={initializeAction} submissionID={1}/>
            </Provider>
        );
        expect(wrapper.find('.container').length).toEqual(1)
        expect(wrapper.find('h3').text()).toBe("Create Determination")
        expect(initializeAction).toHaveBeenCalled()
        expect(initializeAction).toHaveBeenCalledWith(1,null)
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });

    // it("Should render determination with loading false", () => {
    //     store = mockStore({
    //         "Settings": initialState
    //     });
    //     const initializeAction = jest.fn()
    //     const wrapper = mount(
    //         <Provider
    //             store={store}
    //         >
    //             <DeterminationFormContainer formData={{loading : false, saveAsDraft : true, initialValues : [], metaStructure : []}} initializeAction={initializeAction} submissionID={1} determinationId={2}/>
    //         </Provider>
    //     );
    //     expect(wrapper.find('.container').length).toEqual(1)
    //     expect(wrapper.find('h3').text()).toBe("Update Determination")
    //     expect(initializeAction).toHaveBeenCalled()
    //     expect(initializeAction).toHaveBeenCalledWith(1,2)
    //     expect(wrapper.containsMatchingElement(<FormContainer />)).toBe(true)
    //     expect(wrapper).toMatchSnapshot();
    // });
});
