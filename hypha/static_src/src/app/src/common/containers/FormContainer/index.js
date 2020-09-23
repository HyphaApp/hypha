
import * as React from "react";
import FormField from "./components/FormField";
import _ from "underscore";
import * as Actions from './actions';
import * as Selectors from './selectors';
import {bindActionCreators, compose} from "redux";
import {connect} from "react-redux";
import {initializer} from "./helpers";
import injectReducer from '@utils/injectReducer'
import injectSaga from '@utils/injectSaga'
import reducer from './reducer';
import saga from './sagas';
import { withRouter } from 'react-router-dom';
import { parseValues} from './helpers';
import PropTypes from 'prop-types';


class FormContainer extends React.Component {
    constructor() {
        super();
        this.onChange = this.onChange.bind(this);
        this.submitFn = null;
    }

    onSubmit = (actionType, submitFn) => () => {
        const { values, errors} = this.formInfo;
      if (_.isEmpty(errors) && actionType === "primary") {
        this.submitFn = submitFn;
        this.props.validateAndSubmitForm(this.props.formId)
      }
      else if (actionType !== "primary"){
        submitFn(parseValues(this.props.metadata.fields, values))
      }
    }
    
    componentDidUpdate() {
        const { values, errors, readyToSubmit} = this.formInfo;
        if(readyToSubmit && _.isEmpty(errors)) {
          this.submitFn(parseValues(this.props.metadata.fields, values))
        }
    }

    componentDidMount() {
        this.props.initialize(
            this.props.formId,
          initializer(this.props.metadata.fields, this.props.metadata.initialValues)
        );
    }

    onChange(name, value)  {
        this.props.updateFieldValue(this.props.formId, name, value)
    }

    get formInfo() {
        return {
            values: this.props.formsInfo[this.props.formId] ? this.props.formsInfo[this.props.formId].values : {},
            errors: this.props.formsInfo[this.props.formId] ? this.props.formsInfo[this.props.formId].errors : {},
            readyToSubmit: this.props.formsInfo[this.props.formId] ? this.props.formsInfo[this.props.formId].readyToSubmit : false
        }
    }

    render() {
        const formFields = this.props.metadata.fields;
        const actions = this.props.metadata.actions;
        const {errors, values} = this.formInfo;
        return <div>
            {this.props.metadata.title && <h3> {this.props.metadata.title} </h3>}
            <div style={{ width: `${this.props.metadata.width}px` }}>
            <form className="form form--with-p-tags form--scoreable">
                {(formFields || []).map(field => {
                    return <FormField 
                      type={field.type}
                      key={field.id}
                      name={field.kwargs.label}
                      kwargs={field.kwargs}
                      onChange={this.onChange}
                      value={values[field.kwargs.label]}
                      error={errors[field.kwargs.label]}
                      widget={field.widget}
                    />
                })}
                </form>
            </div>

            <div > 
                {(actions || [] ).map(action => {
                  let disabled = false;
                  if (action.type === "primary") {
                    disabled = Object.keys(errors).length > 0
                  }
                  return <input
                    className={`button button--submit button--top-space button--${action.type === 'primary' ? 'primary' : 'white'} ${action.type === 'warning' ? 'button--warning' : ''}`}
                    type="button"
                    disabled={disabled}
                    key={action.text}
                    value={action.text}
                    onClick={this.onSubmit(action.type, action.callback)}
                  />
                })}
            </div>
        </div>;
    }
}

FormContainer.propTypes = {
  formsInfo: PropTypes.object,
  initialize: PropTypes.func,
  updateFieldValue: PropTypes.func,
  validateAndSubmitForm: PropTypes.func,
  formId: PropTypes.string,
  metadata: PropTypes.object,
   
}


const mapStateToProps = state => ({
    formsInfo: Selectors.selectFormsInfo(state),
    activeForm: Selectors.selectActiveForm(state)
});

const mapDispatchToProps = dispatch => {
    return bindActionCreators({
        initialize: Actions.initializeFormAction,
        updateFieldValue: Actions.updateFieldValueAction,
        validateAndSubmitForm: Actions.validateAndSubmitFormAction
    }, dispatch);
}


const withConnect = connect(mapStateToProps, mapDispatchToProps)

const withReducer = injectReducer({ key: 'FormContainer', reducer });
const withSaga = injectSaga({ key: 'FormContainer', saga });

export default compose(
  withSaga,
  withReducer,
  withConnect,
  withRouter,
)(FormContainer);