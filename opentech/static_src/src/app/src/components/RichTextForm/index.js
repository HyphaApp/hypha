import React from 'react';
import PropTypes from 'prop-types';

export default class RichTextForm extends React.Component {
    static defaultProps = {
        disabled: false,
        initialValue: '',
    };

    static propTypes = {
        disabled: PropTypes.bool.isRequired,
        initialValue: PropTypes.string,
        onValueChange: PropTypes.func,
    };

    render() {
        const passProps = {
            disabled: this.props.disabled,
            defaultValue: this.props.initialValue,
            onChange: this.handleValueChange,
        };
        return (
            <textarea {...passProps} />
        );
    }

    handleValueChange = evt => {
        this.props.onValueChange(evt.target.value);
    }
}
