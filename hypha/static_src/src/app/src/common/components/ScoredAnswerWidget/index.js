import * as React from "react";
import DropDown from "@common/components/DropDown";
import TinyMCE from "@common/components/TinyMCE";
import HelperComponent from "@common/components/HelperComponent";
import PropTypes from 'prop-types';



class ScoredAnswerWidget extends React.Component {

  onChange = index => (name, value) => {
    const updatedValue = this.props.value
    updatedValue[index] = value;
    this.props.onChange(this.props.name, updatedValue)
  }

  render() {
    return <div className="form__group ">

      <label htmlFor={this.props.name} className="form__question form__question--scored_answer_field scored_answer_widget">
        <span>{this.props.label}</span>
        {this.props.required ? <span className="form__required"> *</span> : ""}
      </label>
      <HelperComponent {...this.props.helperProps} />

      <div className="form__item">
        <TinyMCE
          name={this.props.name}
          value={this.props.value[0]}
          onChange={this.onChange(0)}
          id={this.props.name}
          init={this.props.widget[0].mce_attrs}
        />
     
        <div className="form__select">
          <DropDown
              name={this.props.name}
              value={this.props.value[1]}
              onChange={this.onChange(1)}
              id={this.props.name}
              choices={this.props.kwargs.fields[1].choices}
          />
        </div>

      </div>
    </div>
  }
}

ScoredAnswerWidget.propTypes = {
  value : PropTypes.node,
  onChange: PropTypes.func,
  name: PropTypes.string,
  label: PropTypes.string,
  required: PropTypes.bool,
  helperProps: PropTypes.node,
  widget: PropTypes.array,
  kwargs:  PropTypes.object
}

ScoredAnswerWidget.displayName = 'ScoredAnswerWidget';
export default ScoredAnswerWidget;
