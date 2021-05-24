import React, {Component} from 'react';
import PropTypes from 'prop-types';


const WithFlagType = (WrappedComponent, type, flagInfo, submissionID) => {
    
    return class Wrapper extends Component{
        render() {
            let title, APIPath
            if(type === "user") {
                title = "Add to your flagged list"
                APIPath = `apply/submissions/${submissionID}/user/flag/`
            } else {
                title = "Add to staff flagged list"
                APIPath = `apply/submissions/${submissionID}/staff/flag/`
            }
            return (
                <WrappedComponent type={type} title={title} APIPath={APIPath} selected={flagInfo.selected}/>
            );
        }
    }
}

WithFlagType.propTypes = {
    WrappedComponent: PropTypes.elementType,
    type: PropTypes.string,
    submissionID: PropTypes.number
}

export default WithFlagType;
