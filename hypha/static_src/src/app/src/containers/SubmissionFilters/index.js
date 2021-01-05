import React from 'react';
import injectReducer from '@utils/injectReducer'
import injectSaga from '@utils/injectSaga'
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import { bindActionCreators, compose } from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
import * as Selectors from './selectors';
import "./styles.scss";
import LoadingPanel from '@components/LoadingPanel';
import Button from '@material-ui/core/Button';
import {clearAllSubmissionsAction} from '@actions/submissions';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';
import { withStyles } from '@material-ui/core/styles';
import Tooltip from '@material-ui/core/Tooltip';
import FilterDropDown from '@common/components/FilterDropDown'

const styles = {
  filterButton: {
      minWidth: 150,
      backgroundColor: "#0c72a0 !important ",
      color: "white",
      marginRight: 10,
      height: 40
  },
};

class SubmissionFiltersContainer extends React.PureComponent {

  componentDidMount(){
    this.props.initializeAction()
  }

  onFilter = () => {
    const options = this.props.submissionFilters.selectedFilters
    let filterQuery = [];
    Object.keys(options).forEach(key => options[key] && 
      filterQuery.push({"key": key, "value": options[key]})
    )
    this.props.updateFilterQuery(filterQuery)
    this.props.onFilter()
  }

  onFilterDelete = () => {
    this.props.deleteSelectedFilters()
    this.onFilter()
    this.props.updateFilterQuery([])
  }
  
  getValue  = filterKey => {
    if(this.props.submissionFilters.selectedFilters && 
      this.props.submissionFilters.selectedFilters.hasOwnProperty(filterKey)) {
        return this.props.submissionFilters.selectedFilters[filterKey].asMutable()
    }
    return []
  }

  renderValues = (selected, filter) => {
    return filter.options
      .filter(option => selected.indexOf(option.key) > -1)
      .map(option => option.label)
      .join(", ")
  }

  handleChange = event => this.props.updateSelectedFilter(event.target.name, event.target.value);
  
  render() {
      const { classes } = this.props;
      return !this.props.submissionFilters.loading ? <div className={"filter-container"}> 
          {this.props.submissionFilters.filters
          .filter(filter => this.props.doNotRender.indexOf(filter.filterKey) === -1 )
          .map(filter => 
            {
              return <FilterDropDown 
                        key={filter.label}
                        filter={filter} 
                        value={this.getValue(filter.filterKey)}
                        handleChange={this.handleChange}
                        renderValues={this.renderValues}
                      />
            })}

          <Button 
            variant="contained" 
            size={"small"}
            classes={{  root : classes.filterButton }} 
            onClick={this.onFilter}
          >
            Filter
          </Button>

          <Tooltip 
            title={<span 
              style={{ fontSize : '15px'}}>
                clear
              </span>} 
              placement="right">
            <HighlightOffIcon 
              style={{ 
                visibility: Object.keys(this.props.submissionFilters.selectedFilters).length !=0 ?
                'visible' : 'hidden'}}
              className={"delete-button"} 
              fontSize="large" 
              onClick={this.onFilterDelete}
            /> 
          </Tooltip>
             
       </div> : <LoadingPanel />
  }
}

SubmissionFiltersContainer.propTypes = {
  submissionFilters: PropTypes.object,
  initializeAction: PropTypes.func,
  updateSelectedFilter: PropTypes.func,
  updateFilterQuery: PropTypes.func,
  onFilter: PropTypes.func,
  doNotRender: PropTypes.array,
  deleteSelectedFilters: PropTypes.func,
  classes: PropTypes.object
}


const mapStateToProps = state =>  ({
    submissionFilters: Selectors.SelectSubmissionFiltersInfo(state),
});


function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      initializeAction: Actions.initializeAction,
      updateSelectedFilter: Actions.updateSelectedFilterAction,
      clearAllSubmissions : clearAllSubmissionsAction,
      updateFilterQuery: Actions.updateFiltersQueryAction,
      deleteSelectedFilters: Actions.deleteSelectedFiltersAction
    },
    dispatch,
  );
}

const withConnect = connect(
  mapStateToProps,
  mapDispatchToProps,
);

const withReducer = injectReducer({ key: 'SubmissionFiltersContainer', reducer });
const withSaga = injectSaga({ key: 'SubmissionFiltersContainer', saga });



export default compose(
  withSaga,
  withReducer,
  withConnect,
  withRouter,
  withStyles(styles)
)(SubmissionFiltersContainer);
