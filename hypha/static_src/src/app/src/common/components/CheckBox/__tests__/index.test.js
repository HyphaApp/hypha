import React from 'react';
import {mount, shallow} from 'enzyme';
import sinon from 'sinon';
import CheckBox from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test CheckBox component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<CheckBox
        name={name}
        label={label}
        required={required}
        value={value}
        helperProps={helperProps}
        onChange = {onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__group').length).toBe(1);
        expect(subject.find('.form__item').length).toBe(1);
        expect(subject.find('form__required').length).toBe(0);
        expect(subject.find('span').text()).toBe(label);
        expect(subject.find('input').prop('checked')).toBe('checked');
        expect(subject.children().length).toEqual(1);
        subject.find('.form__item').props().onClick();
        expect(onChange).toHaveBeenCalledWith(name, false);
        subject.find('input').last().props().onChange({currentTarget: {value: 1}});
        expect(onChange).toHaveBeenCalledWith(name, 1);
        expect(onChange).toHaveBeenCalledTimes(2);
        expect(subject.find('input').props().checked).toEqual('checked');
    });

    test('render a CheckBox component', () => {
        expect(subject).toMatchSnapshot();
    });
});

describe('Test CheckBox component with required', () => {
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<CheckBox
        name={name}
        label={label}
        required={required}
        value={value}
        helperProps={helperProps}
        onChange = {onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and element', () => {
        expect(subject.find('.form__required').length).toBe(1);
    });

    test('render a CheckBox component', () => {
        expect(subject).toMatchSnapshot();
    });
});
