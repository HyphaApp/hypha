import * as React from 'react';

import {Editor} from '@tinymce/tinymce-react';
import HelperComponent from '@common/components/HelperComponent';
import PropTypes from 'prop-types';


const TinyMCE = props => {
    return <div className="form__group ">
        <label htmlFor={props.name} className="form__question form__question--choice_field select" required="">
            <span>{props.label}</span>
            {props.required ? <span className="form__required"> *</span> : ''}
        </label>
        <HelperComponent {...props.helperProps} />
        <Editor
            value={props.value}
            init={{
                ...(props.init),
                menubar: false
            }}
            id={props.name}
            onEditorChange = {content => props.onChange(props.name, content)}
        />
    </div>;
};
TinyMCE.propTypes = {
    label: PropTypes.string,
    required: PropTypes.bool,
    onChange: PropTypes.func,
    value: PropTypes.node,
    helperProps: PropTypes.object,
    init: PropTypes.object,
    name: PropTypes.string
};

TinyMCE.displayName = 'TinyMCE';
export default TinyMCE;
