import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import ListingItem from '../ListingItem';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Listing item component with selected', () => {
    const item = {title: 'Title Text'};
    const selected = true;
    const onClick = jest.fn();

    const subject = mount(<ListingItem item={item}
        selected={selected} onClick={onClick}/>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.is-active').length).toBe(1);
        subject.find('.listing__link').props().onClick();
        expect(onClick).toHaveBeenCalled();
        expect(subject.find('a').text()).toBe(item.title);
    });

    test('render a listing item component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test Listing item component', () => {
    const item = {title: 'Title Text'};
    const selected = false;
    const onClick = jest.fn();

    const subject = mount(<ListingItem item={item}
        selected={selected} onClick={onClick}/>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.is-active').length).toBe(0);
        subject.find('.listing__link').props().onClick();
        expect(onClick).toHaveBeenCalled();
        expect(subject.find('a').text()).toBe(item.title);
    });

    test('render a listing item component', () => {
        expect(subject).toMatchSnapshot();
    });

});
