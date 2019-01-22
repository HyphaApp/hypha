import { combineReducers } from 'redux';

import {
    UPDATE_NOTE,
    UPDATE_NOTES,
    START_FETCHING_NOTES,
    FAIL_FETCHING_NOTES,
} from '@actions/notes';

function notesFetching(state = false, action) {
    switch (action.type) {
        case START_FETCHING_NOTES:
            return true;
        case UPDATE_NOTES:
        case FAIL_FETCHING_NOTES:
            return false;
        default:
            return state;
    }
}


function notesErrored(state = false, action) {
    switch (action.type) {
        case UPDATE_NOTES:
        case START_FETCHING_NOTES:
            return false;
        case FAIL_FETCHING_NOTES:
            return true;
        default:
            return state;
    }
}

function note(state, action) {
    switch (action.type) {
        case UPDATE_NOTE:
            return {
                ...state,
                ...action.data,
            };
        default:
            return state;
    }
}

function notesByID(state = {}, action) {
    switch(action.type) {
        case UPDATE_NOTES:
            return {
                ...state,
                ...action.data.results.reduce((newNotesAccumulator, newNote) => {
                    newNotesAccumulator[newNote.id] = note(state[newNote.id], {
                        type: UPDATE_NOTE,
                        data: newNote,
                    });
                    return newNotesAccumulator;
                }, {}),
            };
        default:
            return state;
    }
}

export default combineReducers({
    byID: notesByID,
    isFetching: notesFetching,
    isErrored: notesErrored,
});
