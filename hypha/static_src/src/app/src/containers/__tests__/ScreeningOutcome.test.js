import React from 'react';
import {mount} from 'enzyme';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});
import {ScreeningOutcome} from '../ScreeningOutcome';

describe('Test screening outcome Container', () => {
    it('Should render screening outcome', () => {
        const submission = {screening: <div>Screening text</div>};
        const wrapper = mount(
            <ScreeningOutcome
                submission={submission}
            />
        );
        expect(wrapper.find('div').length).toEqual(3);
        expect(wrapper.find('.sidebar-block').find('div').first().text().includes('Screening text')).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Should render screening outcome without outcome', () => {
        const submission = {screening: null};
        const wrapper = mount(
            <ScreeningOutcome
                submission={submission}
            />
        );
        expect(wrapper.find('div').length).toEqual(2);
        expect(wrapper.find('.sidebar-block').text().includes('Not yet screened')).toBe(true);
        expect(wrapper).toMatchSnapshot();
    });
});
