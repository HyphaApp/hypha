import * as React from "react";
import PropTypes from 'prop-types';


const LoadHTML = props => {
  return <div className="form__group rich-text">
    <div dangerouslySetInnerHTML={{ __html: props.text }} />
  </div>
}

LoadHTML.propTypes={
  text: PropTypes.string
}

LoadHTML.displayName = 'LoadHTML';
export default LoadHTML;
