import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import MessageList from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import MessageBar from '@components/MessageBar';


describe('Test inline loading component', () => {
    const children = [<MessageBar key={1}/>];
    const subject = mount(<MessageList children={children}></MessageList>
    );

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.messages').length).toBe(1);
        expect(subject.find('ul').length).toBe(1);
    });

    test('render a inline loading component', () => {
        expect(subject).toMatchSnapshot();
    });

});
