import React from 'react';
import {mount, shallow} from 'enzyme';
import sinon from 'sinon';
import FormField from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import TextBox from '@common/components/TextBox';
import DropDown from '@common/components/DropDown';
import Radio from '@common/components/Radio';
import TinyMCE from '@common/components/TinyMCE';
import ScoredAnswerWidget from '@common/components/ScoredAnswerWidget';
import LoadHTML from '@common/components/LoadHTML';
import Textarea from '@common/components/Textarea';
import CheckBox from '@common/components/CheckBox';
import PageDownWidget from '@common/components/PageDownWidget';
import PropTypes from 'prop-types';


describe('Test form field component should render TextBox', () => {
    const fieldProps = {name: 'name text'};
    const value = ['value'];
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: 'EmailInput', mce_attrs: 'mce_attrs1', widgets: []};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = 'type2';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and TextBox component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('TextBox').props().onChange();
        expect(onChange).toHaveBeenCalled();
        expect(subject.containsMatchingElement(<TextBox />)).toEqual(true);
    });

    test('render a form field component with textbox', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render TinyMCE', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: '', mce_attrs: {key: 'mce_attrs1'}, widgets: []};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = 'TinyMCE';

    const subject = shallow(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and TinyMCE component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('TinyMCE').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<TinyMCE />)).toEqual(true);
    });

    test('render a form field component with TinyMCE', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render Textarea', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: 'Textarea', mce_attrs: {key: 'mce_attrs1'}, widgets: [], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = 'Textarea';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and Textarea component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('Textarea').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<Textarea />)).toEqual(true);
    });

    test('render a form field component with Textarea', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render DropDown', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: '', mce_attrs: {key: 'mce_attrs1'}, widgets: [], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = 'Select';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and DropDown component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('DropDown').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<DropDown />)).toEqual(true);
    });

    test('render a form field component with DropDown', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render Radio', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: 'RadioSelect', mce_attrs: {key: 'mce_attrs1'}, widgets: [], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = '';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and Radio component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('Radio').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<Radio />)).toEqual(true);
    });

    test('render a form field component with Radio', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render CheckBox', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: '', mce_attrs: {key: 'mce_attrs1'}, widgets: [], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1'};
    const type = 'CheckboxInput';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and CheckBox component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('CheckBox').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<CheckBox />)).toEqual(true);
    });

    test('render a form field component with CheckBox', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render ScoredAnswerWidget', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: '', mce_attrs: {key: 'mce_attrs1'}, widgets: [{mce_attrs: {key: 'mce_attrs2'}}], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1', fields: [{}, {choices: [1]}]};
    const type = 'ScoredAnswerWidget';

    const subject = shallow(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and ScoredAnswerWidget component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        subject.find('ScoredAnswerWidget').props().onChange('name text', ['value']);
        expect(subject.find('ScoredAnswerWidget').props().value).toEqual([]);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
        expect(subject.containsMatchingElement(<ScoredAnswerWidget />)).toEqual(true);
    });

    test('render a form field component with ScoredAnswerWidget', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render LoadHTML', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: '', mce_attrs: {key: 'mce_attrs1'}, widgets: [{mce_attrs: {key: 'mce_attrs2'}}], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1', fields: [{}, {choices: [1]}]};
    const type = 'LoadHTML';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and LoadHTML component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        expect(subject.containsMatchingElement(<LoadHTML />)).toEqual(true);
    });

    test('render a form field component with LoadHTML', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render PagedownWidget', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: 'PagedownWidget', mce_attrs: {key: 'mce_attrs1'}, widgets: [{mce_attrs: {key: 'mce_attrs2'}}], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1', fields: [{}, {choices: [1]}]};
    const type = '';

    const subject = shallow(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and PagedownWidget component', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        expect(subject.containsMatchingElement(<PageDownWidget />)).toEqual(true);
        subject.find('PageDownWidget').props().onChange('name text', ['value']);
        expect(onChange).toHaveBeenCalled();
        expect(onChange).toHaveBeenCalledWith('name text', ['value']);
    });

    test('render a form field component with PagedownWidget', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test form field component should render unknown type', () => {
    const fieldProps = {name: 'name text'};
    const value = 'value';
    const error = 'error text';
    const onChange = jest.fn();
    const widget = {type: 'none type', mce_attrs: {key: 'mce_attrs1'}, widgets: [{mce_attrs: {key: 'mce_attrs2'}}], attrs: {cols: 1, rows: 1}};
    const kwargs = {help_text: 'help_text', help_link: 'link1', label: 'label1', required: true, choices: [[0, 1]], text: 'text1', fields: [{}, {choices: [1]}]};
    const type = 'PageDownWidget';

    const subject = mount(<FormField
        fieldProps={fieldProps}
        onChange={onChange}
        value={value}
        error={error}
        widget={widget}
        kwargs={kwargs}
        type={type}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes', () => {
        expect(subject.find('.formFieldcontainer').length).toBe(1);
        expect(subject.find('.error').text()).toBe(error);
        expect(subject.find('.formFieldcontainer').first().text().includes('Unknown field type none type')).toBe(true);
        expect(subject.containsMatchingElement(<PageDownWidget />)).toEqual(false);
    });

    test('render a form field component with unknown type passed', () => {
        expect(subject).toMatchSnapshot();
    });

});
