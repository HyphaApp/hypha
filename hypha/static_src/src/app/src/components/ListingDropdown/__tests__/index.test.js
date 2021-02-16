import React from "react";
import { mount } from "enzyme";
import sinon from "sinon";
import ListingDropdown from "../index";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
enzyme.configure({ adapter: new Adapter() });


describe("Test listing drop down component", () => {

    const listRef = { current : 'ul.listing.listing--applications'} 
    const groups = [{
                  items: [1,2],
                  key: "round-37",
                  name: "review api test"
                }]
    const scrollOffset = 75

    const subject = mount(<ListingDropdown
        listRef={listRef}
        groups={groups}
        scrollOffset={scrollOffset}
    />);
  
    it("Shoud render without issues", () => {
      expect(subject.length).toBe(1);
    });
  
    it("Should have searched classes and elements", () => {
      expect(subject.find('.form__select').length).toBe(1);
      expect(subject.find('option').length).toBe(1)
      expect(subject.find('select').children().length).toBe(1)
      expect(subject.find('option').text()).toEqual(groups[0].name)
    });

    // it("test methods ", () => {
    //   const spy = jest.spyOn(ListingDropdown.prototype, 'handleChange');
    //   const wrapper = mount(<ListingDropdown listRef={listRef}
    //     groups={groups}
    //     scrollOffset={scrollOffset} />);
    //   wrapper.instance().handleChange({target: {value : 1}});
    //   expect(spy).toHaveBeenCalled();
    // });
  
    test('render a listing drop down component', () => {
      expect(subject).toMatchSnapshot();
    });
  
  });
