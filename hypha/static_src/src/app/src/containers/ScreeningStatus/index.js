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


class ScreeningStatusContainer extends React.PureComponent {

  componentDidMount(){
    this.props.initializeAction(this.props.submissionID)
    }

    componentDidUpdate(prevProps){
      if(this.props.submissionID != prevProps.submissionID){
        this.props.initializeAction(this.props.submissionID)
      }
    }

  render(){
    const {screeningStatuses, submissionID, selectDefautValue, defaultOptions, screeningInfo, visibleOptions, selectVisibleOption} = this.props
    return !screeningInfo.loading ? screeningStatuses && <SidebarBlock title="Screening Status">
        <div className="screening-status-box" >
        <div style={{ display : "flex", marginBottom: '1em'}}>
        <div className="screening-status-yes" style={{ marginRight : '2em'}}>
            <div>{defaultOptions.yes.title}</div>
            <a disabled={screeningInfo.selectedValues.length} 
            onClick={() => selectDefautValue(submissionID, defaultOptions.yes)} 
            style={{ border : screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id && '1px solid green'}}
            >Up</a>
        </div>
        <div className="screening-status-no">
            <div>{defaultOptions.no.title}</div>
            <a disabled={screeningInfo.selectedValues.length} 
            onClick={() => selectDefautValue(submissionID, defaultOptions.no)} 
            style={{ border : screeningInfo.defaultSelectedValue.id == defaultOptions.no.id && '1px solid red'}}
            >Down</a>
        </div>
        </div>
        {visibleOptions && 
        <div className="screening-visible-options">
          {visibleOptions.map(option => <a key={option.id}  
          onClick={() => selectVisibleOption(submissionID, option)} 
          style={{ margin : '0.4em', border : option.selected && '1px solid black', borderRadius : '4px' }}
          >{option.title}</a>)}
        </div>}
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
