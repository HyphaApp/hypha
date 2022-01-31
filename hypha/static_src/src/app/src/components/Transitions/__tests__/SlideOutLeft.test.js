import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import SlideOutLeft from '../SlideOutLeft';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Slide out left component', () => {

    const children = <span>Children</span>;
    const subject = mount(<SlideOutLeft>{children}</SlideOutLeft>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    test('render a Slide out left component', () => {
        expect(subject).toMatchSnapshot();
    });

});
