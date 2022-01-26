import React from 'react';
import {shallow} from 'enzyme';
import sinon from 'sinon';
import PageDownWidget from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test pagedownwidget component', () => {
    const text = 'test name';
    const name = 'test name';
    const label = 'test label';
    const required = false;
    const helperProps = {};
    const value = '1';
    const id = '1';
    const init = {a: 1};

    const subject = shallow(<PageDownWidget
        id = {id}
        init = {init}
        text={text}
        name={name}
        label={label}
        required={required}
        value={value}
        helperProps={helperProps}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes', () => {
        expect(subject.find('.preview').length).toBe(1);
        expect(subject.children().length).toEqual(2);
    });

    test('render a pagedownwidget component', () => {
        expect(subject).toMatchSnapshot();
    });

});
