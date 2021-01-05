import React from 'react';
import PropTypes from 'prop-types';
// import "./styles.scss";
import Select from '@material-ui/core/Select';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import { withStyles } from '@material-ui/core/styles';
import Checkbox from '@material-ui/core/Checkbox';
import ListItemText from '@material-ui/core/ListItemText';
import Input from '@material-ui/core/Input';

const styles = {
  formControl:{
    minWidth: 200                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       ,
    maxWidth: 200,
    marginRight: 10,
    height: 40
  },
};

class FilterDropDown extends React.PureComponent {

  render() {
    const { filter, value, handleChange, renderValues, classes } = this.props;
    return  <FormControl 
              variant="outlined" 
              key={filter.label} 
              size={"small"}
              classes={{  root : classes.formControl }}
              >
                <InputLabel>{filter.label}</InputLabel>
                <Select
                  multiple
                  name={filter.filterKey}
                  value={value}
                  onChange={handleChange}
                  input={<Input />}
                  renderValue={(selected) => renderValues(selected, filter)}
                >
                  {filter["options"].map(
                    option => <MenuItem 
                      value={option.key} 
                      key={option.key}
                      >
                      <Checkbox 
                        checked={value.indexOf(option.key) > -1}
                        style ={{ color: "#0c72a0b3" }}
                      />
                      <ListItemText primary={option.label} />
                    </MenuItem>
                    )}
                </Select>
              </FormControl>
          }
}


FilterDropDown.propTypes = {
  filter: PropTypes.object,
  value: PropTypes.array,
  handleChange: PropTypes.func,
  renderValues: PropTypes.func,
  classes: PropTypes.object
}

export default withStyles(styles)(FilterDropDown);
