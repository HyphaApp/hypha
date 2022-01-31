import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import Tabber from '../index';
import {Tab} from '@components/Tabber';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Tabber component', () => {

    const children = [
        <Tab button="Status" key="status">
            {/* <span>inside status</span> */}
        </Tab>,
        <Tab button="Notes" key="note"><span>inside note</span></Tab>
    ];

    const subject = mount(<Tabber>{children}</Tabber>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.is-active').text()).toBe('Status');
        expect(subject.find('a').length).toBe(2);
        expect(subject.find('a').last().text()).toBe('Notes');
        subject.find('a').last().props().onClick();
    });

    it('Check methods of the component', () => {
        const spy = jest.spyOn(Tabber.prototype, 'componentDidUpdate');
        const wrapper = shallow(<Tabber children={children}/>).instance();
        wrapper.handleClick(1);
        expect(spy).toHaveBeenCalled();
        spy.mockReset();
        spy.mockRestore();
        expect(wrapper.state.activeTab).toBe(1);

    });

    it('Check handleClick method  of the component', () => {
        const wrapper = shallow(<Tabber children={children}/>).instance();
        wrapper.handleClick = jest.fn();
        wrapper.handleClick(0);
        expect(wrapper.handleClick).toHaveBeenCalled();
        expect(wrapper.handleClick).toHaveBeenCalledWith(0);
        expect(wrapper.state.activeTab).toBe(0);
    });


    test('render a Tabber component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test Tabber component2', () => {

    const children = [
        <Tab button="Status" key="status">
            <span>inside status</span>
        </Tab>,
        <Tab button="Notes" key="note"><span>inside note</span></Tab>
    ];

    const subject = mount(<Tabber>{children}</Tabber>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.is-active').text()).toBe('Status');
        expect(subject.find('a').length).toBe(2);
        expect(subject.find('a').last().text()).toBe('Notes');
        subject.find('a').last().props().onClick();
    });

    it('Check methods of the component', () => {
        const spy = jest.spyOn(Tabber.prototype, 'componentDidUpdate');
        const wrapper = shallow(<Tabber children={children}/>).instance();
        wrapper.handleClick(1);
        expect(spy).toHaveBeenCalled();
        spy.mockReset();
        spy.mockRestore();
        expect(wrapper.state.activeTab).toBe(1);

    });

    it('Check handleClick method  of the component', () => {
        const wrapper = shallow(<Tabber children={children}/>).instance();
        wrapper.handleClick = jest.fn();
        wrapper.handleClick(0);
        expect(wrapper.handleClick).toHaveBeenCalled();
        expect(wrapper.handleClick).toHaveBeenCalledWith(0);
        expect(wrapper.state.activeTab).toBe(0);
    });


    test('render a Tabber component', () => {
        expect(subject).toMatchSnapshot();
    });

});
