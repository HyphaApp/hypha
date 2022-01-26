import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import SubmissionLink from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test submission link component', () => {

    const subject = mount(<SubmissionLink
        submissionID = {1}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.submission-link').length).toBe(1);
        expect(subject.find('a').props().href).toBe('/apply/submissions/1/');
        expect(subject.find('a').children().length).toBe(2);
        expect(subject.find('a').text()).toEqual('Open in new tab');
    });

    test('render a submission link component', () => {
        expect(subject).toMatchSnapshot();
    });

});
