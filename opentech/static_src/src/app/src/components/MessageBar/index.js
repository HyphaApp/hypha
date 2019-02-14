import React from 'react'
import PropTypes from 'prop-types'

import { MESSAGE_TYPES } from '@actions/messages'

const MessageBar = ({ message, type, onDismiss }) => {

    return (
        <div className={type}>
            <p>{message}</p>
            {onDismiss && <button onClick={onDismiss}>[X]</button>}
        </div>
    )
}

MessageBar.propTypes = {
    type: PropTypes.oneOf(Object.values(MESSAGE_TYPES)),
    message: PropTypes.string,
    onDismiss: PropTypes.func,
}

export default MessageBar
