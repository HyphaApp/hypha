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
        instance: PropTypes.string,
        onSubmit: PropTypes.func,
    };

    state = {
        value: RichTextEditor.createEmptyValue(),
    };

    resetEditor = () => {
        this.setState({value: RichTextEditor.createEmptyValue()});
    }

    render() {
        const { instance, disabled } = this.props;

        return (
            <div className={ instance } >
                <RichTextEditor
                    disabled={ disabled }
                    onChange={ this.handleValueChange }
                    value={ this.state.value }
                />
                <button
                    disabled={this.isEmpty() || disabled}
                    onClick={this.handleSubmit}
                    className={`button ${instance}__button`}
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
