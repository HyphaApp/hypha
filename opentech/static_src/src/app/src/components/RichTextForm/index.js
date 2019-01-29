import React from 'react';
import PropTypes from 'prop-types';
import RichTextEditor from 'react-rte';

export default class RichTextForm extends React.Component {
    static defaultProps = {
        disabled: false,
        initialValue: '',
    };

    static propTypes = {
        disabled: PropTypes.bool.isRequired,
        onValueChange: PropTypes.func,
        value: PropTypes.string,
        onSubmit: PropTypes.func,
    };

    state = {
        value: RichTextEditor.createEmptyValue(),
    };

    resetEditor = () => {
        this.setState({value: RichTextEditor.createEmptyValue()});
    }

    render() {
        const passProps = {
            disabled: this.props.disabled,
            onChange: this.handleValueChange,
            value: this.state.value,
        };

        return (
            <div>
                <RichTextEditor {...passProps} />
                <button
                    disabled={this.isEmpty() || this.props.disabled}
                    onClick={this.handleSubmit}
                >
                    Submit
                </button>
            </div>
        );
    }

    isEmpty = () => {
        return !this.state.value;
    }

    handleValueChange = value => {
        this.setState({value});
    }

    handleSubmit = () => {
        this.props.onSubmit(this.state.value.toString('markdown'), this.resetEditor);
    }
}
