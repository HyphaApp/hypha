import React from 'react'
import PropTypes from 'prop-types'

import { MESSAGE_TYPES } from '@actions/messages'


const MessageBar = ({ message, type, onDismiss, dismissMessage='OK' }) => {
    const modifierClass = type ? `messages__text--${type}` : '';
    return (
        <li className={`messages__text ${modifierClass}`}>
            <div className="messages__inner">
                <p className="messages__copy">{message}</p>
                {onDismiss && <button className="button messages__button" onClick={onDismiss}>{dismissMessage}</button>}
            </div>
        </li>
    )
}

MessageBar.propTypes = {
    type: PropTypes.oneOf(Object.values(MESSAGE_TYPES)),
    message: PropTypes.string,
    onDismiss: PropTypes.func,
    dismissMessage: PropTypes.string,
}

export default MessageBar
