import React from 'react'
import { connect } from 'react-redux'

import MessageBar from '@components/MessageBar'
import { getMessages } from '@selectors/messages'
import { dismissMessage } from '@actions/messages'

const MessagesContainer = ({ messages, dismiss }) => {
    return Object.values(messages).map(v =>
        <MessageBar key={v.id} message={v}
            onDismiss={() => dismiss(v.id)} />
    )
}

const mapStateToProps = state => ({
    messages: getMessages(state),
})

const mapDispatchToProps = dispatch => ({
    dismiss: id => dispatch(dismissMessage(id)),
})

export default connect(mapStateToProps, mapDispatchToProps)(MessagesContainer)
