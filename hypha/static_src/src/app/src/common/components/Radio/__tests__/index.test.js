import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import Radio from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test radio component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<Radio
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
        expect(subject.children().length).toEqual(1);
        expect(subject.find('span').text()).toBe(label);
        expect(subject.find('.form__required').length).toBe(0);
        subject.find('li').first().props().onClick();
        expect(onChange).toHaveBeenCalledWith(name, '1');
        expect(onChange).toHaveBeenCalled();
        subject.find('input').last().props().onChange();
        expect(onChange).toHaveBeenCalledWith(name, '2');
        expect(onChange).toHaveBeenCalledTimes(2);
    });

    test('render a radio component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test radio component with required & empty choices', () => {
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const choices = [];
    const helperProps = {};
    const value = '1';
    const onChange = jest.fn();

    const subject = mount(<Radio
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
        expect(subject.children().length).toEqual(1);
        expect(subject.find('span').first().text()).toBe(label);
        expect(subject.find('.form__required').length).toBe(1);
        expect(subject.find('li').length).toBe(0);
        expect(subject.find('input').length).toBe(0);
        expect(choices.length).toBe(0);
    });

    test('render a radio component with required & empty choices', () => {
        expect(subject).toMatchSnapshot();
    });

});
