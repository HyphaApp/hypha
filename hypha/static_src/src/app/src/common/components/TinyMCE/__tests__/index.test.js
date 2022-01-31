import React from 'react';
import {shallow} from 'enzyme';
import sinon from 'sinon';
import TinyMCE from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import {Editor} from '@tinymce/tinymce-react';
import HelperComponent from '@common/components/HelperComponent';


describe('Test tinymce component', () => {
    const text = 'test name';
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const helperProps = {};
    const value = 'abc';
    const init = {a: 1};
    const onChange = jest.fn();

    const subject = shallow(<TinyMCE
        init = {init}
        text={text}
        name={name}
        label={label}
        required={required}
        value={value}
        helperProps={helperProps}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have select and span element with passed text', () => {
        expect(subject.find('.form__required').length).toBe(0);
        expect(subject.children().length).toEqual(3);
        expect(subject.find('span').first().text()).toBe(label);
        expect(subject.containsMatchingElement(<Editor />)).toEqual(true);
        expect(subject.containsMatchingElement(<HelperComponent />)).toEqual(true);
        expect(subject.find('Editor').length).toEqual(1);
        subject.find('Editor').props().onEditorChange(1);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith(name, 1);
    });

    test('render a TinyMCE component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test tinymce component with required', () => {
    const text = 'test name';
    const name = 'test name';
    const label = 'test label';
    const required = true;
    const helperProps = {};
    const value = 'abc';
    const init = {a: 1};
    const onChange = jest.fn();

    const subject = shallow(<TinyMCE
        init = {init}
        text={text}
        name={name}
        label={label}
        required={required}
        value={value}
        helperProps={helperProps}
        onChange={onChange}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have select and span element with passed text', () => {
        expect(subject.find('.form__required').length).toBe(1);
    });

    test('render a TinyMCE component with required', () => {
        expect(subject).toMatchSnapshot();
    });

});
