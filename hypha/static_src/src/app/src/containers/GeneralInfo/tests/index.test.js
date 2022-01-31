import React from 'react';
import {mount} from 'enzyme';
import {Provider} from 'react-redux';
import configureMockStore from 'redux-mock-store';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import initialState from '../models';
import {GeneralInfoContainer} from '../index.js';

enzyme.configure({adapter: new Adapter()});

const mockStore = configureMockStore();
describe('Test General info Container', () => {
    let store;
    const locale = 'en-US';
    it('Should render General info without issues', () => {
        store = mockStore({
            Settings: initialState
        });
        const initializeAction = jest.fn();
        const wrapper = mount(
            <Provider
                store={store}
            >
                <GeneralInfoContainer initializeAction={initializeAction}/>
            </Provider>
        );
        expect(wrapper.find('.container').length).toEqual(0);
        expect(initializeAction).toHaveBeenCalled();
        expect(wrapper).toMatchObject({});
        expect(wrapper).toMatchSnapshot();
    });
});
