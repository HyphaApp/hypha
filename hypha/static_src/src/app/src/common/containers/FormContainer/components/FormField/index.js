import * as React from "react";
import  "./index.scss";
import TextBox from "@common/components/TextBox";
import DropDown from "@common/components/DropDown";
import Radio from "@common/components/Radio";
import TinyMCE from "@common/components/TinyMCE";
import ScoredAnswerWidget from "@common/components/ScoredAnswerWidget";
import LoadHTML from "@common/components/LoadHTML";
import Textarea from "@common/components/Textarea";
import CheckBox from "@common/components/CheckBox";
import PropTypes from 'prop-types';


import _ from "lodash";

class FormField extends React.Component {
  static propTypes = {
    onChange: PropTypes.func,
    widget: PropTypes.object,
    kwargs: PropTypes.object,
    value: PropTypes.node,
    error: PropTypes.string,
    fieldProps: PropTypes.object,
    type: PropTypes.string,

  }

    onChange = (name, value) => {
      this.props.onChange(name, value)
    }

    getType() {
      return this.props.widget && this.props.widget.type ? this.props.widget.type : this.props.type;
    }

    getHelperprops() {
      return {
        text: this.props.kwargs.help_text,
        link: this.props.kwargs.help_link,
      }
    }

    renderField() {
        const {value, kwargs, widget,  ...fieldProps} = this.props;
      switch (this.getType()) {
          case "EmailInput":
          case "URLInput":
          case "TextInput":
            return <TextBox 
              label={kwargs.label}
              required={kwargs.required}
              name={fieldProps.name}
              value={value}
              onChange={this.onChange}
              id={fieldProps.name}
              helperProps={this.getHelperprops()}
            />;

          case "TinyMCE":
            return <TinyMCE 
              label={kwargs.label}
              name={fieldProps.name}
              onChange={this.onChange}
              value={value}
              id={fieldProps.name}
              init={widget.mce_attrs}
              required={kwargs.required}
              helperProps={this.getHelperprops()}
              
            />;

        case "Textarea":
          return <Textarea
            label={kwargs.label}
            name={fieldProps.name}
            onChange={this.onChange}
            value={value}
            id={fieldProps.name}
            widget={widget}
            required={kwargs.required}
            helperProps={this.getHelperprops()}
            
          />;
            
        case "Select":
          return <DropDown 
            label={kwargs.label}
            name={fieldProps.name}
            value={value}
            onChange={this.onChange}
            id={fieldProps.name}
            choices={kwargs.choices}
            required={kwargs.required}
            helperProps={this.getHelperprops()}
            
          />;

        case "RadioSelect":
          return <Radio 
            value={value}
            help_text={kwargs.help_text}
            label={kwargs.label}
            choices={kwargs.choices}
            name={fieldProps.name}
            onChange={this.onChange}
            required={kwargs.required}
            helperProps={this.getHelperprops()}
            
          />;

        case "CheckboxInput":
          return <CheckBox
            value={value}
            help_text={kwargs.help_text}
            label={kwargs.label}
            choices={kwargs.choices}
            name={fieldProps.name}
            onChange={this.onChange}
            required={kwargs.required}
            helperProps={this.getHelperprops()}
            
          />;
          
        case "ScoredAnswerWidget":
          return <ScoredAnswerWidget
            value={_.isArray(value) ? value.asMutable() : []}
            help_text={kwargs.help_text}
            label={kwargs.label}
            name={fieldProps.name}
            onChange={this.onChange}
            kwargs={kwargs}
            widget={widget.widgets}
            required={kwargs.required}
            helperProps={this.getHelperprops()}
            
          />;

        case "LoadHTML":
          return <LoadHTML 
            text={kwargs.text}
          />;
      
        default:
          return <div>Unknown field type {this.getType()}</div>
        }
    }
        
    render() {
        return <div  > 
            {this.renderField()}
            <div className="error">
                {this.props.error}
            </div>
        </div>
    }
}

    
export default FormField;
    
