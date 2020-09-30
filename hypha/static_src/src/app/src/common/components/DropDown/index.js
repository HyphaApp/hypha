import * as React from "react";
import PropTypes from 'prop-types';

import HelperComponent from "@common/components/HelperComponent";


const DropDown = props => {
  return <div className="form__group ">
    <label htmlFor={props.name} className="form__question form__question--choice_field select" required="">
      <span>{props.label}</span>
      {props.required ? <span className="form__required"> *</span> : ""}
    </label>
    <HelperComponent {...props.helperProps} />
    
    <div className="form__item">
      <div className="form__select">
        <select
          name={props.name}
          id={props.name}
          onChange={e => props.onChange(props.name, e.currentTarget.value)}
          value = { props.value }
        >
          {(props.choices || []).map(choice => {
            return <option key={choice[0]} value={choice[0]} >{choice[1]}</option>
          })}
        </select>
      </div>
    </div>
  </div>
}
DropDown.propTypes = {
  name: PropTypes.string,
  label: PropTypes.string,
  onChange: PropTypes.func,
  required: PropTypes.bool,
  choices: PropTypes.array,
  helperProps: PropTypes.object,
  value: PropTypes.node
}

DropDown.displayName = 'DropDown';
export default DropDown;
