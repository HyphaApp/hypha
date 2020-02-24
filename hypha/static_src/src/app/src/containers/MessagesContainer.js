import React from 'react'
import { connect } from 'react-redux'
import PropTypes from 'prop-types'

import MessageBar from '@components/MessageBar'
import MessagesList from '@components/MessagesList'
import { getMessages } from '@selectors/messages'
import { dismissMessage } from '@actions/messages'

const MessagesContainer = ({ messages, dismiss }) => {
    return (
        <MessagesList>
            {Object.values(messages).map(({ message, type, id}) =>
                <MessageBar key={id} message={message} type={type}
                    onDismiss={() => dismiss(id)} />
            )}
        </MessagesList>
    )
}

const mapStateToProps = state => ({
    messages: getMessages(state),
})

const mapDispatchToProps = dispatch => ({
    dismiss: id => dispatch(dismissMessage(id)),
})

MessagesContainer.propTypes = {
    messages: PropTypes.object,
    dismiss: PropTypes.func,
}

export default connect(mapStateToProps, mapDispatchToProps)(MessagesContainer)
