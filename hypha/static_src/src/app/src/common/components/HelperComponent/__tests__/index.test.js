import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import HelperComponent from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test Helper component', () => {
    const text = 'test name';
    const link = '';

    const subject = mount(<HelperComponent
        text={text}
        link={link}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes', () => {
        expect(subject.find('.form__help').length).toBe(1);
        expect(subject.find('.form__help-link').length).toBe(0);
        expect(subject.children().length).toEqual(1);
    });

    test('render a Helper component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test Helper component with link', () => {
    const text = 'test name';
    const link = 'sdfsd';

    const subject = mount(<HelperComponent
        text={text}
        link={link}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes', () => {
        expect(subject.find('.form__help-link').length).toBe(1);
    });

    test('render a Helper component with link', () => {
        expect(subject).toMatchSnapshot();
    });

});
