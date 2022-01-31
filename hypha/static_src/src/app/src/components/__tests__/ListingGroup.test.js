import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import ListingGroup from '../ListingGroup';
import ListingHeading from '../ListingHeading';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Listing Group component', () => {
    const item = {name: 'title text'};
    const id = 'id';
    const children = [<span key={1}>Children</span>];
    const subject = mount(<ListingGroup item={item} id={id} children={children}>
    </ListingGroup>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('li').props().id).toBe(id);
        expect(subject.containsMatchingElement(<ListingHeading />)).toEqual(true);

        expect(subject.find('ListingHeading').first().props().title).toBe(item.name);
        expect(subject.find('ListingHeading').first().props().count).toBe(1);

        expect(subject.find('ul').length).toBe(1);
    });

    test('render a listing group component', () => {
        expect(subject).toMatchSnapshot();
    });

});
