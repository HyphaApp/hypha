import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import MessageBar from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test inline loading component', () => {
    const message = 'message text';
    const dismissMessage = 'dismiss message';
    const onDismiss = jest.fn();
    const type = 'success';

    const subject = mount(<MessageBar
        message={message}
        dismissMessage={dismissMessage}
        onDismiss={onDismiss}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.messages__text--success').length).toBe(1);
        subject.find('button').props().onClick();
        expect(onDismiss).toHaveBeenCalled();
        expect(subject.find('button').text()).toBe(dismissMessage);
    });

    test('render a inline loading component', () => {
        expect(subject).toMatchSnapshot();
    });

});
