import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import Select from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import {Option} from '../index';

describe('Test select component', () => {
    const options = [{display: 'display1', value: 'value1'}];
    const onChange = jest.fn();

    const subject = mount(<Select
        options={options}
        onChange={onChange}

    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('select').length).toBe(1);
        expect(subject.find('option').first().text()).toBe('---');
        subject.find('select').props().onChange({target: {value: 1}});
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith(1);
        expect(subject.containsMatchingElement(<Option />)).toEqual(true);
    });

    test('render a select component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test Option in select component', () => {
    const value = 'value1';
    const display = 'display';

    const subject = mount(<Option
        value={value}
        display={display}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('option').text()).toBe(display);
        expect(subject.find('option').props().value).toBe(value);
    });

    test('render a Option in select component', () => {
        expect(subject).toMatchSnapshot();
    });

});

