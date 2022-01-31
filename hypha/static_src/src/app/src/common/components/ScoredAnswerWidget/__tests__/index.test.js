import React from 'react';
import {shallow} from 'enzyme';
import sinon from 'sinon';
import ScoredAnswerWidget from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
// import  "../index.scss";
import TinyMCE from '@common/components/TinyMCE';
import DropDown from '@common/components/DropDown';


describe('Test scoredanswerwidget component', () => {
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = ['3', 4];
    const widget = ['a', 'b'];
    const kwargs = {fields: [{id: 1}, {choices: [1, 2]}]};
    const onChange = jest.fn();

    const subject = shallow(<ScoredAnswerWidget
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        widget={widget}
        kwargs={kwargs}
        onChange = {onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__group').length).toBe(1);
        expect(subject.find('.form__required').length).toBe(0);
        expect(subject.children().length).toEqual(3);
        expect(subject.find('span').first().text()).toBe(label);
        expect(subject.containsMatchingElement(<TinyMCE />)).toEqual(true);

        subject.find('TinyMCE').props().onChange();
        expect(onChange).toHaveBeenCalledWith(name, [undefined, 4]);
        expect(onChange).toHaveBeenCalled();
        subject.find('DropDown').last().props().onChange();
        expect(onChange).toHaveBeenCalledWith(name, [undefined, undefined]);
        expect(onChange).toHaveBeenCalledTimes(2);
    });

    test('render a scoredAnswerWidget component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test scoredanswerwidget component with required', () => {
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const choices = [['1', 'one'], ['2', 'two']];
    const helperProps = {};
    const value = ['3', 4];
    const widget = ['a', 'b'];
    const kwargs = {fields: [{id: 1}, {choices: [1, 2]}]};
    const onChange = jest.fn();

    const subject = shallow(<ScoredAnswerWidget
        name={name}
        label={label}
        required={required}
        choices={choices}
        value={value}
        helperProps={helperProps}
        widget={widget}
        kwargs={kwargs}
        onChange = {onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and span element with passed text', () => {
        expect(subject.find('.form__required').length).toBe(1);
    });

    test('render a scoredAnswerWidget component with required', () => {
        expect(subject).toMatchSnapshot();
    });

});
