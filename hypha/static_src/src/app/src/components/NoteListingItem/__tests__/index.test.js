import React from 'react';
import {mount} from 'enzyme';
import sinon from 'sinon';
import NoteListingItem from '../index';
import * as enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
enzyme.configure({adapter: new Adapter()});


describe('Test note listing item component', () => {
    const author = 'author text';
    const message = 'message text';
    const handleEditNote = jest.fn();
    const timestamp = '20210127';
    const disabled = false;
    const editable = true;
    const edited = 'true';

    const subject = mount(<NoteListingItem
        author={author}
        message={message}
        handleEditNote={handleEditNote}
        timestamp={timestamp}
        disabled={disabled}
        editable={editable}
        edited={edited}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.note disabled').length).toBe(0);
        expect(subject.find('span').first().text().includes(author)).toBe(true);
        expect(subject.find('.note__edit').length).toBe(1);
        subject.find('a').props().onClick({preventDefault: () => 1});
        expect(handleEditNote).toHaveBeenCalled();
    });

    test('render a note listing item component', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test note listing item component with author text length greater than 16', () => {
    const author = 'author text author text';
    const message = 'message text';
    const handleEditNote = jest.fn();
    const timestamp = '20210127';
    const disabled = false;
    const editable = true;
    const edited = 'true';

    const subject = mount(<NoteListingItem
        author={author}
        message={message}
        handleEditNote={handleEditNote}
        timestamp={timestamp}
        disabled={disabled}
        editable={editable}
        edited={edited}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.disabled').length).toBe(0);
        expect(subject.find('span').first().text().includes('author text auth...')).toEqual(true);
        expect(subject.find('.note__edit').length).toBe(1);
        subject.find('a').props().onClick({preventDefault: () => 1});
        expect(handleEditNote).toHaveBeenCalled();
    });

    test('render a note listing item component with author text length greater than 16', () => {
        expect(subject).toMatchSnapshot();
    });

});

describe('Test note listing item component with disabled prop', () => {
    const author = 'author text';
    const message = 'message text';
    const handleEditNote = jest.fn();
    const timestamp = '20210127';
    const disabled = true;
    const editable = true;
    const edited = 'true';

    const subject = mount(<NoteListingItem
        author={author}
        message={message}
        handleEditNote={handleEditNote}
        timestamp={timestamp}
        disabled={disabled}
        editable={editable}
        edited={edited}
    />);

    it('Shoud render without issues', () => {
        expect(subject.length).toBe(1);
    });

    it('Should have searched classes and elements', () => {
        expect(subject.find('.disabled').length).toBe(1);
        expect(subject.find('span').first().text().includes(author)).toBe(true);
        expect(subject.find('.note__edit').length).toBe(1);
        subject.find('a').props().onClick({preventDefault: () => 1});
        expect(handleEditNote).toHaveBeenCalled();
    });

    test('render a note listing item component with disabled prop', () => {
        expect(subject).toMatchSnapshot();
    });

});
