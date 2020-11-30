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
import { SidebarBlock } from '@components/SidebarBlock'
import LoadingPanel from '@components/LoadingPanel'
import Chip from '@material-ui/core/Chip';
import DoneIcon from '@material-ui/icons/Done';
import ThumbUpIcon from '@material-ui/icons/ThumbUp';
import ThumbDownIcon from '@material-ui/icons/ThumbDown';

class ScreeningStatusContainer extends React.PureComponent {

  componentDidMount(){
    if(this.props.submissionID){
      this.props.initializeAction(this.props.submissionID)
    }
  }

  componentDidUpdate(prevProps){
    if(this.props.submissionID != prevProps.submissionID){
      this.props.initializeAction(this.props.submissionID)
    }
  }
  updateDefaultValue = (submissionID, defaultOption) => () => {
    if(!this.props.screeningInfo.selectedValues.length && 
          this.props.screeningInfo.defaultSelectedValue.id != defaultOption.id) 
          {
            this.props.selectDefautValue(submissionID, defaultOption)
          }
    }

  render(){
    const {
      screeningStatuses, 
      submissionID, 
      defaultOptions, 
      screeningInfo, 
      visibleOptions, 
      selectVisibleOption } = this.props

    return !screeningInfo.loading ? screeningStatuses && <SidebarBlock title="Screening Status">
        <div className="screening-status-box" >
          <div className="screening-default-options">
            <div 
              className={screeningInfo.selectedValues.length ||
                screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id ? 
                "screening-status-yes-disabled": "screening-status-yes-enabled"} 
              onClick={this.updateDefaultValue(submissionID, defaultOptions.yes)} 
            >
                <ThumbUpIcon 
                className = { screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id ? "thumbs-up-color" : ""}
                />
                <div>{defaultOptions.yes.title}</div>
            </div>
            <div 
              className={screeningInfo.selectedValues.length || 
                screeningInfo.defaultSelectedValue.id == defaultOptions.no.id ? 
                "screening-status-no-disabled" :"screening-status-no-enabled"}  
              onClick={this.updateDefaultValue(submissionID, defaultOptions.no)} 
            >
                <ThumbDownIcon 
                className = { screeningInfo.defaultSelectedValue.id == defaultOptions.no.id ? "thumbs-down-color" : ""}
                />
                <div>{defaultOptions.no.title}</div>
            </div>
          </div>
          {visibleOptions && 
            <div className="screening-visible-options" >
              <h6 style={{ fontWeight: '550', width : '100%'}}>Screening reasons</h6>
              {visibleOptions.map(option => 
                <Chip 
                style={{ margin : '0.3em'}}
                label={option.title} 
                variant={!option.selected ? "outlined" : "default"} 
                key={option.id}  
                icon={option.selected && <DoneIcon />}
                onClick={() => selectVisibleOption(submissionID, option)}>
                </Chip>)
              }
            </div>
          }
        </div>
    </SidebarBlock> : <LoadingPanel />
  }
}

ScreeningStatusContainer.propTypes = {
  initializeAction: PropTypes.func,
  submission: PropTypes.object,
  selectDefautValue: PropTypes.func,
  defaultOptions: PropTypes.object,
  screeningInfo: PropTypes.object,
  visibleOptions: PropTypes.object,
  selectVisibleOption: PropTypes.func,
  submissionID : PropTypes.number,
  screeningStatuses: PropTypes.array
}


const mapStateToProps = state =>  ({
  screeningInfo : Selectors.selectScreeningInfo(state),
  screeningStatuses : Selectors.selectScreeningStatuses(state),
  defaultOptions : Selectors.selectDefaultOptions(state),
  visibleOptions : Selectors.selectVisibleOptions(state)
  });


function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      initializeAction: Actions.initializeAction,
      selectDefautValue: Actions.selectDefaultValueAction,
      selectVisibleOption: Actions.selectVisibleOptionAction
    },
    dispatch,
  );
}

const withConnect = connect(
  mapStateToProps,
  mapDispatchToProps,
);

const withReducer = injectReducer({ key: 'ScreeningStatusContainer', reducer });
const withSaga = injectSaga({ key: 'ScreeningStatusContainer', saga });


export default compose(
  withSaga,
  withReducer,
  withConnect,
  withRouter,
)(ScreeningStatusContainer);
