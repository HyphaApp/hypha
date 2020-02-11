import React, {useState, useEffect} from 'react';
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


const emptyState = RichTextEditor.createEmptyValue().toString('html')


const RichTextForm = ({initialValue, onChange, onCancel, onSubmit, instance, disabled}) => {
    const [value, updateValue] = useState(RichTextEditor.createValueFromString(initialValue, 'html'))

    useEffect(() => {
        updateValue(RichTextEditor.createValueFromString(initialValue, 'html'))
    }, [initialValue])

    const resetEditor = () => {
        updateValue(RichTextEditor.createEmptyValue())
    }

    const isEmpty = () => {
        return !value.getEditorState().getCurrentContent().hasText();
    }

    const handleValueChange = (newValue) => {
        const html = newValue.toString('html')
        if ( html !== emptyState || value.toString('html') !== emptyState ) {
            onChange && onChange(html)
        }
        updateValue(newValue)
    }

    const handleCancel = () => {
        onCancel();
        resetEditor()
    }

    const handleSubmit = () => {
        onSubmit(value.toString('html'), resetEditor);
    }

    return (
        <div className={ instance } >
            <RichTextEditor
                disabled={ disabled }
                onChange={ handleValueChange }
                value={ value }
                className="add-note-form__container"
                toolbarClassName="add-note-form__toolbar"
                editorClassName="add-note-form__editor"
                toolbarConfig={toolbarConfig}
            />
            <div>
                <button
                    disabled={isEmpty() || disabled}
                    onClick={handleSubmit}
                    className={`button ${instance}__button`}
                >
                    Submit
                </button>
                <button
                    disabled={disabled}
                    onClick={handleCancel}
                    className={`button ${instance}__button`}
                >
                    Cancel
                </button>
            </div>
        </div>
    );

}

RichTextForm.defaultProps = {
    disabled: false,
    initialValue: '',
};

RichTextForm.propTypes = {
    disabled: PropTypes.bool.isRequired,
    onValueChange: PropTypes.func,
    value: PropTypes.string,
    instance: PropTypes.string,
    onSubmit: PropTypes.func,
    onChange: PropTypes.func,
    onCancel: PropTypes.func,
    initialValue: PropTypes.string,
};


export default RichTextForm;
