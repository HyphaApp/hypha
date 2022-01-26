import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import FullScreenLoadingPanel from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import LoadingPanel from '@components/LoadingPanel';


describe('Test full screen loading component', () => {

    const subject = mount(<FullScreenLoadingPanel
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and component', () => {
        expect(subject.find('.full-screen-loading-panel').length).toBe(1);
        expect(subject.containsMatchingElement(<LoadingPanel />)).toEqual(true);
    });

    test('render a full screen loading component', () => {
        expect(subject).toMatchSnapshot();
    });

});
