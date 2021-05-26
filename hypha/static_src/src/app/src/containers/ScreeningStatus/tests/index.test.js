import React from "react";
import {mount} from "enzyme";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import  {ScreeningStatusContainer}  from '../index.js';
import { SidebarBlock } from '@components/SidebarBlock'
import LoadingPanel from '@components/LoadingPanel'
enzyme.configure({adapter: new Adapter()});

describe("Test screening status Container", () => {
    it("Should render screening statuses with loading", () => {
        const wrapper = mount(
                <ScreeningStatusContainer 
                    screeningInfo={{loading : true}}
                    submissionID={1}
                    allScreeningStatuses={null}
                    submissionScreening={null}/>
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(0)
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });

    it("Should render screening statuses with loading false & defaultoptions empty", () => {
        const defaultOptions ={}
        const wrapper = mount(
                <ScreeningStatusContainer 
                screeningInfo={{loading : false}} 
                submissionID={1}
                defaultOptions={defaultOptions}
                />
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(0)
        expect(wrapper.containsMatchingElement(<SidebarBlock />)).toBe(false)
        expect(wrapper).toMatchObject({})
        expect(wrapper).toMatchSnapshot();
    });

    it("Should render screening statuses with Sidebarblock", () => {
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
                defaultOptions={defaultOptions}
                visibleOptions={visibleOptions}
                selectVisibleOption={selectVisibleOption}
                />
        );
        expect(wrapper.find('.screening-status-box').length).toEqual(1)
        expect(wrapper).toMatchObject({})
        expect(wrapper).toMatchSnapshot();
    });
});
