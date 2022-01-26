import * as React from 'react';
import PropTypes from 'prop-types';
import HelperComponent from '@common/components/HelperComponent';
import {withStyles} from '@material-ui/core/styles';
import {DatePicker, MuiPickersUtilsProvider} from '@material-ui/pickers';
import DateFnsUtils from '@date-io/date-fns';

const styles = {
    textField: {
        width: '385px'
    }
};

const DateTime = props => {
    const [selectedDate, handleDateChange] = React.useState(new Date());

    return <div className="form__group  form__group--datetime form__group--wrap">
        <label
            htmlFor={props.name}
            className="form__question form__question--boolean_field datetime_input">
            <span>{props.label}</span>
            {props.required ? <span className="form__required"> *</span> : ''}
        </label>
        <div className="form__item">
            <MuiPickersUtilsProvider utils={DateFnsUtils}>
                <DatePicker
                    className={props.classes.textField}
                    onChange={e => {handleDateChange(e); props.onChange(props.name, new Date(e).toISOString());}}
                    name={props.name}
                    id={props.name}
                    value={selectedDate}
                    format={'Y-MM-d'}
                />
            </MuiPickersUtilsProvider>
        </div>
        <HelperComponent {...props.helperProps} />
    </div>;
};

DateTime.propTypes = {
    name: PropTypes.string,
    label: PropTypes.string,
    required: PropTypes.bool,
    onChange: PropTypes.func,
    value: PropTypes.node,
    helperProps: PropTypes.object,
    classes: PropTypes.object
};

DateTime.displayName = 'DateTime';
export default withStyles(styles)(DateTime);
