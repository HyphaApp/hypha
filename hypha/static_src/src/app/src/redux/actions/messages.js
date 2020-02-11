import uuidv4 from 'uuid/v4';

export const MESSAGE_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info',
}

export const ADD_MESSAGE = 'ADD_MESSAGE'
export const DISMISS_MESSAGE = 'DISMISS_MESSAGE'

export const addMessage = (message, type) => {
    if (!Object.values(MESSAGE_TYPES).includes(type)) {
        throw "Invalid message type"
    }

    return{
        type: ADD_MESSAGE,
        messageType: type,
        messageID: uuidv4(),
        message,
    }
};

export const dismissMessage = messageID => ({
    type: DISMISS_MESSAGE,
    messageID,
});
