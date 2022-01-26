import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import DropDown from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test DropDown component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<DropDown
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__group').length).toBe(1);
        expect(subject.find('select').length).toBe(1);
        expect(subject.find('span').text()).toBe(label);
        expect(subject.children().length).toEqual(1);
        subject.find('select').props().onChange({currentTarget: {value: 1}});
        expect(onChange).toHaveBeenCalled();
    });

    test('render a DropDown component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test DropDown component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<DropDown
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__required').length).toBe(1);
    });

    test('render a DropDown component', () => {
        expect(subject).toMatchSnapshot();
    });

});
