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
import { getGroupedIconStatus, getSubmissions } from '@selectors/submissions';
import IconButton from '@material-ui/core/IconButton';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import MoreVertIcon from '@material-ui/icons/MoreVert';
import { getScreeningLoading } from '@containers/ScreeningStatus/selectors'
import Snackbar from '@material-ui/core/Snackbar';
import MuiAlert from '@material-ui/lab/Alert';
import Slide from '@material-ui/core/Slide';


const Alert = React.forwardRef((props, ref) => 
<MuiAlert elevation={6} variant="filled" {...props} ref={ref} />);

Alert.displayName = 'AlertComponent';

function TransitionRight(props) {
  return <Slide {...props} direction="left" />;
}

const styles = {
  filterButton: {
      minWidth: 150,
      backgroundColor: "#0c72a0 !important ",
      color: "white",
      marginRight: 10,
      height: 40
  },
  share:{
    marginRight: 10,
    height: 40
  }
};

export class SubmissionFiltersContainer extends React.PureComponent {

  state = {
    options : [{key:"applications-summary-list", value : "Applications summary list"},{ key:"share-this-filter", value: "Share this filter"}],
    anchorEl : null,
    openSnackbar: false,
    vertical: 'bottom',
    horizontal: 'center',
  }

  componentDidMount(){
    this.props.initializeAction()
  }

  componentDidUpdate(prevProps, prevState){
    if(
      !this.props.isGroupedIconShown &&
     this.props.history.location.search.includes("&") 
      && !this.props.submissionFilters.loading){
      this.props.initializeAction(this.props.history.location.search, this.onFilter)
    }
  }


  onFilter = () => {
    const options = this.props.submissionFilters.selectedFilters
    let filterQuery = [];
    Object.keys(options).forEach(key => options[key] && 
      filterQuery.push({"key": "f_"+key, "value": options[key]})
    )
    this.props.updateFilterQuery(filterQuery)
    if(!filterQuery.length) this.props.history.push(window.location.pathname)
    this.props.onFilter()
  }

  onFilterDelete = () => {
    this.props.history.push(window.location.pathname)
    this.props.deleteSelectedFilters()
    this.onFilter()
    this.props.updateFilterQuery([])
  }
  
  getValue  = filterKey => {
    if(Object.keys(this.props.submissionFilters.selectedFilters).length && 
      this.props.submissionFilters.selectedFilters.hasOwnProperty(filterKey)) {
        if(filterKey == "status"){
          return this.props.submissionFilters.selectedFilters[filterKey].map(val =>  val.asMutable().sort().join(",")).asMutable()
        }
        return this.props.submissionFilters.selectedFilters[filterKey].asMutable()
    }
    return []
  }

  handleMenuClick = (event) => {
    this.setState({anchorEl: event.currentTarget});
  };

  handleMenuClose = () => {
    this.setState({anchorEl: null});
  };

  renderValues = (selected, filter) => {
    return filter.options
      .filter(option => selected.indexOf(option.key) > -1)
      .map(option => option.label)
      .join(", ")
  }

  handleChange = event => {
    let name = event.target.name;
    let values = event.target.value;
    if (name === 'status') {
      values = values.map(value => value.split(",").sort())
    }
    this.props.updateSelectedFilter(name, values)
  }

  handleMenuitemClick = (option) => e => {
    if(option.key == "share-this-filter") {
      this.setState({ openSnackbar: true })
      navigator.clipboard.writeText((window.location.href));
      e.preventDefault();
      this.handleMenuClose();
      return false;
    }
    this.handleMenuClose();
    return true;
  }
  
  render() {
      const { classes } = this.props;
      const { vertical, horizontal, openSnackbar } = this.state;
      return !this.props.submissionFilters.loading ? <div className={"filter-container"}>
          {this.props.getFiltersToBeRendered
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
          
          {this.props.isGroupedIconShown && Object.keys(this.props.submissions).length != 0 &&
          <>
               <IconButton
                  aria-label="more"
                  aria-controls="long-menu"
                  aria-haspopup="true"
                  onClick={this.handleMenuClick}
                  classes={{  root : classes.share }} 
                >
                  <MoreVertIcon fontSize="large"/>
                </IconButton>
                <Menu
                  id="long-menu"
                  anchorEl={this.state.anchorEl}
                  keepMounted
                  open={Boolean(this.state.anchorEl)}
                  onClose={this.handleMenuClose}
                  PaperProps={{
                    style: {
                      maxHeight: 48 * 4.5,
                      width: '20ch',
                    },
                  }}
                >
                  {this.state.options.map((option) => (
                    <MenuItem 
                      key={option.key} 
                      selected={option.key === "applications-summary-list"} 
                      style={{whiteSpace: 'normal'}}
                    >
                        <a 
                          style={{color: "black", width: "inherit"}}
                          target="_blank" rel="noreferrer" 
                          href={"/apply/submissions/summary/?id="+ Object.keys(this.props.submissions).join(",")}
                          onClick={this.handleMenuitemClick(option)}
                        >
                          {option.value}
                        </a>
                    </MenuItem>
                ))}
              </Menu>
          </>
          }

          <Snackbar
            anchorOrigin={{ vertical, horizontal }}
            autoHideDuration={6000} 
            open={openSnackbar}
            onClose={() => this.setState({openSnackbar: false})}
            key={vertical + horizontal}
            TransitionComponent={TransitionRight}
          >
            <Alert onClose={() => this.setState({openSnackbar: false})} severity="success">
              URL copied to Clipboard!
            </Alert>
          </Snackbar>

          <Tooltip 
            title={<span 
              style={{ fontSize : '15px'}}>
                clear
              </span>} 
              placement="bottom">
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
  classes: PropTypes.object,
  isGroupedIconShown: PropTypes.bool,
  submissions: PropTypes.object,
  getFiltersToBeRendered: PropTypes.array,
  getScreeningLoading: PropTypes.bool,
  history: PropTypes.object
}


const mapStateToProps = state =>  ({
    submissionFilters: Selectors.SelectSubmissionFiltersInfo(state),
    isGroupedIconShown : getGroupedIconStatus(state),
    submissions: getSubmissions(state),
    getScreeningLoading: getScreeningLoading(state),
    getFiltersToBeRendered: Selectors.SelectFiltersToBeRendered(state)
});


function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      initializeAction: Actions.initializeAction,
      updateSelectedFilter: Actions.updateSelectedFilterAction,
      clearAllSubmissions : clearAllSubmissionsAction,
      updateFilterQuery: Actions.updateFiltersQueryAction,
      deleteSelectedFilters: Actions.deleteSelectedFiltersAction,
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
