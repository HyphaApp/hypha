import React from 'react'
import PropTypes from 'prop-types'

import { MESSAGE_TYPES } from '@actions/messages'

const MessageBar = ({message, onDismiss}) => {

    return (
        <div className={message.type}>
            <p>{message.message}</p>
            {onDismiss && <button onClick={onDismiss}>[X]</button>}
        </div>
    )
}

MessageBar.propTypes = {
    message: PropTypes.shape({
        type: PropTypes.oneOf(Object.values(MESSAGE_TYPES)),
        message: PropTypes.string
    }),
    onDismiss: PropTypes.func,
}

export default MessageBar
