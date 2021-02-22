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
import SvgIcon from '@material-ui/core/SvgIcon';

export class ScreeningStatusContainer extends React.PureComponent {

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

    return !screeningInfo.loading ?
        screeningStatuses && defaultOptions.yes && defaultOptions.no ? <SidebarBlock title="Screening Status" >
        <div className="screening-status-box" style={{ padding: '1rem'}}>
          <div className="screening-default-options" >
            <div
              className={screeningInfo.selectedValues.length ||
                screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id ?
                "screening-status-yes-disabled": "screening-status-yes-enabled"}
              onClick={this.updateDefaultValue(submissionID, defaultOptions.yes)}
            >
                <SvgIcon
                  className = { screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id ? "thumbs-up-color" : ""}
                  style={{ alignSelf: 'center'}}
                >
                  <path d="m1.75 23h2.5c.965 0 1.75-.785 1.75-1.75v-11.5c0-.965-.785-1.75-1.75-1.75h-2.5c-.965 0-1.75.785-1.75 1.75v11.5c0 .965.785 1.75 1.75 1.75z"></path><path d="m12.781.75c-1 0-1.5.5-1.5 3 0 2.376-2.301 4.288-3.781 5.273v12.388c1.601.741 4.806 1.839 9.781 1.839h1.6c1.95 0 3.61-1.4 3.94-3.32l1.12-6.5c.42-2.45-1.46-4.68-3.94-4.68h-4.72s.75-1.5.75-4c0-3-2.25-4-3.25-4z"></path>
                </SvgIcon>
                <div
                  className = { screeningInfo.defaultSelectedValue.id == defaultOptions.yes.id ? "screening-status-active" : ""}
                >{defaultOptions.yes.title}</div>
            </div>
            <div
              className={screeningInfo.selectedValues.length ||
                screeningInfo.defaultSelectedValue.id == defaultOptions.no.id ?
                "screening-status-no-disabled" :"screening-status-no-enabled"}
              onClick={this.updateDefaultValue(submissionID, defaultOptions.no)}
            >
                <SvgIcon
                className = { screeningInfo.defaultSelectedValue.id == defaultOptions.no.id ? "thumbs-down-color" : ""}
                style={{ alignSelf: 'center'}}
                >
                  <path d="m22.25 1h-2.5c-.965 0-1.75.785-1.75 1.75v11.5c0 .965.785 1.75 1.75 1.75h2.5c.965 0 1.75-.785 1.75-1.75v-11.5c0-.965-.785-1.75-1.75-1.75z"></path><path d="m5.119.75c-1.95 0-3.61 1.4-3.94 3.32l-1.12 6.5c-.42 2.45 1.46 4.68 3.94 4.68h4.72s-.75 1.5-.75 4c0 3 2.25 4 3.25 4s1.5-.5 1.5-3c0-2.376 2.301-4.288 3.781-5.273v-12.388c-1.601-.741-4.806-1.839-9.781-1.839z"></path>
                </SvgIcon>
                <div
                  className = { screeningInfo.defaultSelectedValue.id == defaultOptions.no.id ? "screening-status-active" : ""}
                >{defaultOptions.no.title}</div>
            </div>
          </div>
          {visibleOptions.length > 0 &&
            <div className="screening-visible-options" >
              <h6 style={{ fontWeight: '550', width : '100%'}}>Screening reasons</h6>
              {visibleOptions.map(option =>
                <Chip
                style={{ margin : '0.3em'}}
                label={option.title}
                variant={!option.selected ? "outlined" : "default"}
                key={option.id}
                icon={option.selected ? <DoneIcon /> : null}
                onClick={() => selectVisibleOption(submissionID, option)}>
                </Chip>)
              }
            </div>
          }

        </div>
      </SidebarBlock> : null
    : <LoadingPanel />
  }
}

ScreeningStatusContainer.propTypes = {
  initializeAction: PropTypes.func,
  submission: PropTypes.object,
  selectDefautValue: PropTypes.func,
  defaultOptions: PropTypes.object,
  screeningInfo: PropTypes.object,
  visibleOptions: PropTypes.array,
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
