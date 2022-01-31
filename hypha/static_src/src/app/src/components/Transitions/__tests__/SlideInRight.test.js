import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import SlideInRight from '../SlideInRight';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Slide in right component', () => {

    const children = <span>Children</span>;
    const subject = mount(<SlideInRight>{children}</SlideInRight>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    test('render a Slide in right component', () => {
        expect(subject).toMatchSnapshot();
    });

});
