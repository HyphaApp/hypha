import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import ListingHeading from '../ListingHeading';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});

describe('Test Listing Heading component', () => {
    const title = 'Title Text';
    const count = '1';
    const subject = mount(<ListingHeading title={title} count={count}/>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.listing__item--heading').length).toBe(1);
        expect(subject.find('.listing__item--heading').props().id).toEqual('title-text');

        expect(subject.find('h5').text()).toBe(title);
        expect(subject.find('div').children().length).toBe(2);
        expect(subject.find('span').text()).toBe(count);
    });

    test('render a listing heading component', () => {
        expect(subject).toMatchSnapshot();
    });

});
