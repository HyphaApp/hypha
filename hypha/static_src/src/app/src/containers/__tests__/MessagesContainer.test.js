import React from 'react';
import {mount} from 'enzyme';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import {MessagesContainer} from '../MessagesContainer';
import MessageBar from '@components/MessageBar';

describe('Test messages Container', () => {
    it('Should render messages outcome', () => {
        const messages = {m: {message: 'message1', type: 'success', id: 1}};
        const dismiss = jest.fn();
        const wrapper = mount(
            <MessagesContainer
                messages={messages}
                dismiss={dismiss}
            />
        );
        wrapper.find('button').props().onClick();
        expect(dismiss).toHaveBeenCalled();
        expect(dismiss).toHaveBeenCalledWith(1);
        expect(wrapper.containsMatchingElement(<MessageBar />)).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });
});
