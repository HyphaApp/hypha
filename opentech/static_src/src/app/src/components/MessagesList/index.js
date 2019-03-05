import React from 'react'
import PropTypes from 'prop-types'

import MessageBar from '@components/MessageBar'

const MessagesList = ({ children }) => {
    return (
        <ul className="messages">
            { children }
        </ul>
    )
}

MessagesList.propTypes = {
    children: PropTypes.oneOfType([PropTypes.arrayOf(MessageBar), MessageBar])
}

export default MessagesList
