import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import FilterDropDown from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test Filter dropdown component', () => {
    const name = 'test name';
    const filter = {
        label: 'label text',
        filterKey: 'filter-key',
        options: [{label: 'op1', key: 1}, {label: 'op2', key: 2}, {label: 'op3', key: 3}]
    };
    const value = ['1'];
    const renderValues = (selected, filter) => {
        return filter.options
            .filter(option => selected.indexOf(option.key) > -1)
            .map(option => option.label)
            .join(', ');
    };

    const subject = mount(<FilterDropDown
        name={name}
        filter={filter}
        value={value}
        renderValues = {renderValues}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have select and label element with passed text', () => {
        expect(subject.find('select').length).toBe(0);
        expect(subject.find('label').text()).toBe(filter.label);
        expect(subject.children().length).toEqual(1);
    });

    test('render a Filter dropdown component', () => {
        expect(subject).toMatchSnapshot();
    });

});
