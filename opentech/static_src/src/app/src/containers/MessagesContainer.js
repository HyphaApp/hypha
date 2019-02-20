import React from 'react'
import { connect } from 'react-redux'

import MessageBar from '@components/MessageBar'
import { getMessages } from '@selectors/messages'
import { dismissMessage } from '@actions/messages'

const MessagesContainer = ({ messages, dismiss }) => {
    return Object.values(messages).map(({ message, type, id}) =>
        <MessageBar key={id} message={message} type={type}
            onDismiss={() => dismiss(id)} />
    )
}

const mapStateToProps = state => ({
    messages: getMessages(state),
})

const mapDispatchToProps = dispatch => ({
    dismiss: id => dispatch(dismissMessage(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(MessagesContainer)
