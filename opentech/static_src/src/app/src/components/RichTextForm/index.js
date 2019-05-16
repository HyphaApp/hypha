import React from 'react';
import PropTypes from 'prop-types';
import RichTextEditor from 'react-rte';

const toolbarConfig = {
    display: ['INLINE_STYLE_BUTTONS', 'BLOCK_TYPE_BUTTONS', 'BLOCK_TYPE_DROPDOWN', 'LINK_BUTTONS'],
    INLINE_STYLE_BUTTONS: [
        {label: 'Bold', style: 'BOLD', className: 'custom-css-class'},
        {label: 'Italic', style: 'ITALIC'},
        {label: 'Underline', style: 'UNDERLINE'},
        {label: 'Blockquote', style: 'blockquote'},

    ],
    BLOCK_TYPE_DROPDOWN: [
        {label: 'Normal', style: 'unstyled'},
        {label: 'H1', style: 'header-four'},
        {label: 'H2', style: 'header-five'},
    ],
    BLOCK_TYPE_BUTTONS: [
        {label: 'UL', style: 'unordered-list-item'},
        {label: 'OL', style: 'ordered-list-item'}
    ]
};

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
        onChange: PropTypes.func,
        onCancel: PropTypes.func,
        initialValue: PropTypes.string,
    };

    state = {
        value: RichTextEditor.createEmptyValue(),
        emptyState: RichTextEditor.createEmptyValue().toString('html'),
    };

    componentDidMount() {
        const {initialValue} = this.props

        if (initialValue) {
            this.setState({ value: RichTextEditor.createValueFromString(initialValue, 'html') });
        }
    }

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
                    className="add-note-form__container"
                    toolbarClassName="add-note-form__toolbar"
                    editorClassName="add-note-form__editor"
                    toolbarConfig={toolbarConfig}
                />
                <div>
                    <button
                        disabled={this.isEmpty() || disabled}
                        onClick={this.handleSubmit}
                        className={`button ${instance}__button`}
                    >
                        Submit
                    </button>
                    <button
                        disabled={this.isEmpty() || disabled}
                        onClick={this.handleCancel}
                        className={`button ${instance}__button`}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        );
    }

    isEmpty = () => {
        return !this.state.value.getEditorState().getCurrentContent().hasText();
    }

    handleValueChange = (value) => {
        const html = value.toString('html')
        if (html !== this.state.emptyState ) {
            this.props.onChange && this.props.onChange(html)
            this.setState({value});
        }
    }

    handleCancel = () => {
        this.props.onCancel();
        this.resetEditor()
    }

    handleSubmit = () => {
        this.props.onSubmit(this.state.value.toString('html'), this.resetEditor);
    }
}
