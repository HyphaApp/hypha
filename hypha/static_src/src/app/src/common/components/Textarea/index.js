import * as React from "react";
import PropTypes from 'prop-types';

import HelperComponent from "@common/components/HelperComponent";


const Textarea = props => {
  return <div className="form__group ">
    <div className="form__group  form__group--wrap" data-word-limit="1000">
      <label htmlFor={props.name} className="form__question form__question--char_field textarea">
        <span>{props.label} </span>
        {props.required ? <span className="form__required"> *</span> : ""}
      </label>
      <HelperComponent {...props.helperProps}/>
      <div className="form__item">
        <textarea 
          cols={props.widget.attrs.cols}
          rows={props.widget.attrs.rows}
          id={props.name}
          value={props.value}
          onChange={e => props.onChange(props.name, e.currentTarget.value)}
          />
    </div>
  </div>
  </div>
}
Textarea.propTypes={
  name: PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  helperProps: PropTypes.node,
  onChange: PropTypes.func,
  value: PropTypes.node,
  widget: PropTypes.object
}

Textarea.displayName = 'Textarea';
export default Textarea;
