import React from "react";
import {mount} from "enzyme";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import  {ScreeningStatusContainer}  from '../index.js';
import { SidebarBlock } from '@components/SidebarBlock'
import LoadingPanel from '@components/LoadingPanel'
enzyme.configure({adapter: new Adapter()});

describe("Test screening decision container", () => {
    it("Should render review form with loading", () => {
        const initializeAction = jest.fn()
        const wrapper = mount(
                <ScreeningStatusContainer screeningInfo={{loading : true}} initializeAction={initializeAction} submissionID={1}/>
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(0)
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });

    it("Should render review form with loading false & defaultoptions empty", () => {
        const initializeAction = jest.fn()
        const defaultOptions ={}
        const wrapper = mount(
                <ScreeningStatusContainer
                screeningInfo={{loading : false}}
                initializeAction={initializeAction}
                submissionID={1}
                defaultOptions={defaultOptions}
                />
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(0)
        expect(initializeAction).toHaveBeenCalled()
        expect(initializeAction).toHaveBeenCalledWith(1)
        expect(wrapper.containsMatchingElement(<SidebarBlock />)).toBe(false)
        expect(wrapper).toMatchObject({})
        expect(wrapper).toMatchSnapshot();
    });

    it("Should render review form with Sidebarblock", () => {
        const initializeAction = jest.fn()
        const selectVisibleOption = jest.fn()
        const defaultOptions ={
            yes : { id : 1, title : "a"},
            no  : { id : 2, title : "b"}
        }
        const screeningInfo = {
            loading : false,
            selectedValues : [1],
            defaultSelectedValue : { id : 1 }
        }
        const visibleOptions = [{
            title : "title1",
            selected : false,
            id : 3,
            yes : true
        },
        {
            title : "title2",
            selected : false,
            id : 4,
            yes : true
        }]
        const wrapper = mount(
                <ScreeningStatusContainer
                screeningStatuses={[1,2]}
                screeningInfo={screeningInfo}
                initializeAction={initializeAction}
                defaultOptions={defaultOptions}
                visibleOptions={visibleOptions}
                selectVisibleOption={selectVisibleOption}
                />
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(1)
        expect(initializeAction).not.toHaveBeenCalled()
        expect(wrapper).toMatchObject({})
        expect(wrapper).toMatchSnapshot();
    });
});
