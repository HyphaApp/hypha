import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import TextArea from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test textarea component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = '1';
    const widget = {attrs: {cols: 'a', rows: 'c'}};
    const kwargs = {fields: [{id: 1}, {choices: [1, 2]}]};
    const onChange = jest.fn();


    const subject = mount(<TextArea
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        widget={widget}
        kwargs={kwargs}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__group').length).toBe(2);
        expect(subject.find('.form__required').length).toBe(0);
        expect(subject.children().length).toEqual(1);
        expect(subject.find('span').first().text()).toBe(label);
        subject.find('textarea').props().onChange({currentTarget: {value: 1}});
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith(name, 1);
    });

    test('render a TextArea component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test textarea component with required', () => {
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = '1';
    const widget = {attrs: {cols: 'a', rows: 'c'}};
    const kwargs = {fields: [{id: 1}, {choices: [1, 2]}]};
    const onChange = jest.fn();


    const subject = mount(<TextArea
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        widget={widget}
        kwargs={kwargs}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__required').length).toBe(1);
    });

    test('render a TextArea component with required', () => {
        expect(subject).toMatchSnapshot();
    });

});
