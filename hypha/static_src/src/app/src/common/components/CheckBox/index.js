import * as React from "react";
import PropTypes from 'prop-types';

import HelperComponent from "@common/components/HelperComponent";


const CheckBox = props => {
  return <div className="form__group  form__group--checkbox form__group--wrap">

    <label 
      htmlFor={props.name}
      className="form__question form__question--boolean_field checkbox_input">
        <span>{props.label}</span>
         {props.required ? <span className="form__required"> *</span> : ""}
      </label>


    <div className="form__item" 
      onClick={e => props.onChange(props.name, !props.value)}
    >
      <input 
        type="checkbox" 
        name={props.name}
        id={props.name}
        checked={props.value ? "checked" : ""}
        onChange={e => props.onChange(props.name, e.currentTarget.value)}
      />
      <label />
    </div>
    <hr />
    <HelperComponent {...props.helperProps} />

  </div>
}

CheckBox.propTypes = {
  name: PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  value: PropTypes.node,
  helperProps: PropTypes.node
}

CheckBox.displayName = 'CheckBox';
export default CheckBox;
