import * as React from "react";

import { Editor } from '@tinymce/tinymce-react';
import HelperComponent from "@common/components/HelperComponent";
import PropTypes from 'prop-types';


const TinyMCE = props => {
  return <div className="form__group ">
    <label htmlFor={props.name} className="form__question form__question--choice_field select" required="">
      <span>{props.label} </span>
      {props.required ? <span className="form__required"> *</span> : ""}
    </label>
    <HelperComponent {...props.helperProps} />
    <Editor
      initialValue={props.value}
      init={{
        ...(props.mce_attrs),
        menubar: false
      }}
      onChange={e => props.onChange(props.name, e.level.content)}
      id={props.name}
    />
  </div>
}
TinyMCE.propTypes = {
  label: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  value: PropTypes.node,
  helperProps: PropTypes.object,
  name: PropTypes.string,
  mce_attrs: PropTypes.node
}

TinyMCE.displayName = 'TinyMCE';
export default TinyMCE;
