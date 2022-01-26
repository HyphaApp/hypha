import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import InlineLoading from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import OTFLoadingIcon from '@components/OTFLoadingIcon';


describe('Test inline loading component', () => {

    const subject = mount(<InlineLoading
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.loading-inline').length).toBe(1);
        expect(subject.containsMatchingElement(<OTFLoadingIcon />)).toEqual(true);
    });

    test('render a inline loading component', () => {
        expect(subject).toMatchSnapshot();
    });

});
