import React from "react";
import {mount} from "enzyme";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
import  {SubmissionFiltersContainer}  from '../index.js';
import LoadingPanel from '@components/LoadingPanel';
import FilterDropDown from '@common/components/FilterDropDown'
import * as Immutable from 'seamless-immutable';
enzyme.configure({adapter: new Adapter()});

describe("Test submission filter Container", () => {
    it("Should render submission filter with loading true", () => {
        const initializeAction = jest.fn()
        const wrapper = mount(
                <SubmissionFiltersContainer submissionFilters={{loading : true}} initializeAction={initializeAction}/>
        );
        expect(wrapper.find('.filter-container').length).toEqual(0)
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(true)
        expect(wrapper).toMatchSnapshot();
    });

    it("Should render submission filter with loading false", () => {
        const initializeAction = jest.fn()
        const updateSelectedFilter = jest.fn()
        const updateFilterQuery = jest.fn()
        const onFilter = jest.fn()
        const deleteSelectedFilters = jest.fn()

        const doNotRender = []
        const submissionFilters = Immutable.from({
            loading : false,
            selectedFilters : {
                1 : []
            },
            filters :[{filterKey : "key1", label : "label1", options: [{key : 1, label: "label2"}]}]
        })
        const classes = {
            filterButton : "string"
        }
        const wrapper = shallow(
                <SubmissionFiltersContainer 
                submissionFilters={submissionFilters} 
                initializeAction={initializeAction}
                updateSelectedFilter={updateSelectedFilter}
                updateFilterQuery={updateFilterQuery}
                onFilter={onFilter}
                doNotRender={doNotRender}
                deleteSelectedFilters={deleteSelectedFilters}
                classes={classes}
                getFiltersToBeRendered={[{filterKey : "key1", label : "label1", options: [{key : 1, label: "label2"}]}]}
                />
        );

        expect(wrapper.find('.filter-container').length).toEqual(1)
        expect(initializeAction).toHaveBeenCalled()
        expect(wrapper.containsMatchingElement(<LoadingPanel />)).toBe(false)
        expect(wrapper.containsMatchingElement(<FilterDropDown />)).toBe(true)
        const subObj = wrapper.instance()
        subObj.handleChange({target : { name : "name1", value : "value1" } })
        expect(updateSelectedFilter).toHaveBeenCalled()
        expect(updateSelectedFilter).toHaveBeenCalledWith("name1", "value1")
        expect(wrapper).toMatchSnapshot();
    });
});
