import * as React from "react";
import PropTypes from 'prop-types';

import HelperComponent from "@common/components/HelperComponent";


const TextBox = props => {
  return <div className="form__group ">
    <label htmlFor={props.id} className="form__question form__question--char_field text_input" >
      <span>{props.label}</span>
      {props.required ? <span className="form__required"> *</span> : ""}
    </label>
    <HelperComponent {...props.helperProps} />

    <div className="form__item">
      <input
        type="text"
        name={props.name}
        value={props.value ? props.value : ""}
        onChange={e => props.onChange(props.name, e.currentTarget.value)}
        id={props.id}
      />
    </div>
  </div>
}

TextBox.propTypes = {
  id : PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  value: PropTypes.node,
  helperProps: PropTypes.node,
  name: PropTypes.string,
}

TextBox.displayName = 'TextBox';
export default TextBox;
