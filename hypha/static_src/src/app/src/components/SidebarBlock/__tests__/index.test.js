import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import SidebarBlock from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Side bar component', () => {
    const title = 'title text';

    const subject = mount(<SidebarBlock title={title}>
        <span>Children</span></SidebarBlock>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.sidebar-block').length).toBe(1);
        expect(subject.find('h5').text()).toBe(title);
        expect(subject.find('div').children().length).toBe(4);
        expect(subject.find('span').text()).toBe('Children');
    });

    test('render a side bar component', () => {
        expect(subject).toMatchSnapshot();
    });

});
