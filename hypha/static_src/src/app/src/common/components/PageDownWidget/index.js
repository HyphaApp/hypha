import * as React from "react";
import PropTypes from 'prop-types';
import  TinyMCE  from '../TinyMCE';
import  "./index.scss";

const PageDownWidget = props => {
  let tmp = document.createElement("DIV");
  tmp.innerHTML = props.value;
  return <div >
        <TinyMCE 
        label={props.label}
        name={props.name}
        onChange={props.onChange}
        value={props.value}
        id={props.id}
        init={props.init}
        required={props.required}
        helperProps={props.helperProps}
        />
   
        { tmp.textContent.length !== 0 &&
    <div className="preview" dangerouslySetInnerHTML={{__html: props.value}}>
      
    </div>}
  </div>

}
PageDownWidget.propTypes = {
  id: PropTypes.string,
  init: PropTypes.object,
  label: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  value: PropTypes.node,
  helperProps: PropTypes.object,
  name: PropTypes.string,
  
}

PageDownWidget.displayName = 'PageDownWidget';
export default PageDownWidget;
