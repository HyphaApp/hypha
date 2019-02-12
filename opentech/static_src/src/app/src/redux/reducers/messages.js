import { combineReducers } from 'redux'

import { ADD_MESSAGE, DISMISS_MESSAGE } from '@actions/messages';

const message = (state, action) => {
    switch (action.type) {
        case ADD_MESSAGE:
            return {
                ...state,
                id: action.messageID,
                messageType: action.messageType,
                message: action.message,
            }
        default:
            return state
    }
}

const messages = (state = {}, action) => {
    switch(action.type) {
        case ADD_MESSAGE:
            return {
                ...state,
                [action.messageID]: message(
                    state[action.messageID], action
                ),
            }
        case DISMISS_MESSAGE:
            return Object.entries(state).reduce((acc, [k, v]) => {
                if(k !== action.messageID) {
                    acc[k] = v
                }
                return acc
            }, {})
        default:
            return state
    }
}

export default combineReducers({
    messages,
})
