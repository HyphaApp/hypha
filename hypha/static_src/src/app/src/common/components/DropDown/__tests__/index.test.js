import React from "react";
import { mount } from "enzyme";
import sinon from "sinon";
import DropDown from "../index";
import * as enzyme from "enzyme";
import Adapter from "enzyme-adapter-react-16";
enzyme.configure({ adapter: new Adapter() });


describe("Test Header compnent", () => {
  const name = "test name";
  const label = "test label";
  const required = false;
  const choices = [["1", "one"], ["2", "two"]];
  const helperProps = {};
  const value = "1";

  const subject = mount(<DropDown
    name={name}
    label={label}
    required={required}
    choices={choices}
    value={value}
    helperProps={helperProps}
  />);

  it("Shoud render without issues", () => {
    expect(subject.length).toBe(1);
  });

  it("Should have select and span element with passed text", () => {
    expect(subject.find('.form__group').length).toBe(1);
    expect(subject.find('select').length).toBe(1);
    expect(subject.find('span').text()).toBe(label);
  });

  test('render a Header with title and description', () => {
    expect(subject).toMatchSnapshot();
  });

});
