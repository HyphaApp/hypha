import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import RichTextForm from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import RichTextEditor from 'react-rte';


describe('Test select component', () => {
    const disabled = false;
    const initialValue = '';
    const onSubmit = jest.fn();
    const onChange = jest.fn();
    const onCancel = jest.fn();
    const instance = 'add-text';

    const subject = mount(<RichTextForm
        disabled={disabled}
        onChange={onChange}
        initialValue={initialValue}
        onSubmit={onSubmit}
        onCancel={onCancel}
        instance={instance}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.add-text').length).toBe(1);
        //   console.log(subject.find('.add-note-form__container').debug())
        expect(subject.find('.add-text__button').first().text()).toBe('Submit');
        expect(subject.find('button').last().text()).toBe('Cancel');
        subject.find('.add-text__button').first().props().onClick();
        expect(onSubmit).toHaveBeenCalled();
        subject.find('.add-text__button').last().props().onClick();
        expect(onCancel).toHaveBeenCalled();
        expect(subject.containsMatchingElement(<RichTextEditor />)).toEqual(true);
    });

    // it("Check handleValueChange method  of the component", () => {
    //     const wrapper = shallow(<RichTextForm
    //         disabled={disabled}
    //         onChange={onChange}
    //         initialValue={initialValue}
    //         onSubmit={onSubmit}
    //         onCancel={onCancel}
    //         instance={instance}
    //       />).instance();
    //     // wrapper.handleValueChange = jest.fn()
    //     wrapper.handleValueChange("hello");
    //     expect(onChange).toHaveBeenCalled();
    //     // expect(wrapper.handleValueChange).toHaveBeenCalledWith("hello");
    //     // expect(wrapper.state.activeTab).toBe(0);
    //   });


    // test('render a select component', () => {
    //   expect(subject).toMatchSnapshot();
    // });

});
