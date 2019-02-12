import React from 'react';
import PropTypes from 'prop-types';

export default class Modal extends React.Component {
    static propTypes = {
        heading: PropTypes.string,
        content: PropTypes.node.isRequired,
        visible: PropTypes.bool,
        onClose: PropTypes.func,
    }

    get styles() {
        const { visible } = this.props;
        const modalStyle = {};

        if (!visible) {
            modalStyle['display'] = 'none';
        }

        return {
            modal: {
                ...modalStyle
            }
        }
    }

    render() {
        const { content, heading, onClose } = this.props;
        return (
            <div style={this.styles.modal}>
                {onClose && <button onClick={onClose}>[X]</button>}
                {heading && <h1>{heading}</h1>}
                {content}
            </div>
        );
    }
}
