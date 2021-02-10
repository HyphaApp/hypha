
import Enzyme, {shallow, render, mount} from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
//import expect from 'expect';
import React from "react";

// React 15 Enzyme adapter
Enzyme.configure({adapter: new Adapter()});
// Make Enzyme functions available in all test files without importing
global.shallow = shallow;
global.render = render;
global.mount = mount;
//global.expect = expect;
global.React = React;
global.mashup = {
    notifications: {
        addNotification: (options) => {
            if (options.onRemove) {options.onRemove();}
        }
    }
};
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    clear: jest.fn()
};
global.localStorage = localStorageMock;

// Fail tests on any warning
// console.error = message => {
//     throw new Error(message);
// };
