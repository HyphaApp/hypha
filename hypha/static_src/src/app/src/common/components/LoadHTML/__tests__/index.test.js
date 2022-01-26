import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import LoadHTML from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test loadHTML component', () => {
    const text = 'test name';

    const subject = mount(<LoadHTML
        text={text}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes ', () => {
        expect(subject.find('.form__group').length).toBe(1);
        expect(subject.children().length).toEqual(1);
    });

    test('render a loadHTML component', () => {
        expect(subject).toMatchSnapshot();
    });

});
