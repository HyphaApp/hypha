import * as React from "react";
import PropTypes from 'prop-types';
import HelperComponent from "@common/components/HelperComponent";


const DropDown = props => {
  return <div className="form__group ">
    <label htmlFor={props.name} className="form__question form__question--choice_field radio_select" required="">
      <span>{props.label}</span>
      {props.required ? <span className="form__required"> *</span> : ""}
    </label>
    
    <HelperComponent {...props.helperProps} />

    <div className="form__item">
      <ul className="grid grid--no-margin grid--two" >
        {(props.choices || []).map((choice, key) => {
          return <li className="form__item" key={key} onClick={e => props.onChange(props.name, choice[0])}>
          <input 
            type="radio" 
            name={props.name}
            value={choice[0]}
            checked={props.value === choice[0] ? "checked" : ""}
            onChange={e => props.onChange(props.name, choice[0])}
          />
          <label className="form__label" htmlFor={`${props.name}-${key}`}>{choice[1]}</label>
        </li>;
        })}
      </ul>

    </div>
  </div>
}

DropDown.propTypes = {
  name: PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  value: PropTypes.node,
  helperProps: PropTypes.object,
  choices: PropTypes.array,
}

DropDown.displayName = 'DropDown';
export default DropDown;
