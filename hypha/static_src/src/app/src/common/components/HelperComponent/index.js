import * as React from "react";
import PropTypes from 'prop-types';


const HelperComponent = props => {
  return <>
    {props.text && <p className="form__help" dangerouslySetInnerHTML={{ __html: props.text }} />}
    {props.link && <p className="form__help-link">
      <a href={props.link} target="_blank" rel="noopener noreferrer">See help guide for more information.
        <svg className="form__open-icon"><use href="#open-in-new-tab"></use></svg>
      </a>
    </p>}
  </>
}
HelperComponent.propTypes = {
  text: PropTypes.string,
  link: PropTypes.node
}

HelperComponent.displayName = 'HelperComponent';
export default HelperComponent;
 