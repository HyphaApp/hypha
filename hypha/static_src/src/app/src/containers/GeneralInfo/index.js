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



class GeneralInfoContainer extends React.PureComponent {

  componentDidMount(){
    this.props.initializeAction()
    }

  render(){
      return null
  }
}

GeneralInfoContainer.propTypes = {
  user: PropTypes.object,
  initializeAction: PropTypes.func,
}


const mapStateToProps = state =>  ({
    user: Selectors.selectGeneralInfo(state),
  });


function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      initializeAction: Actions.initializeAction,
    },
    dispatch,
  );
}

const withConnect = connect(
  mapStateToProps,
  mapDispatchToProps,
);

const withReducer = injectReducer({ key: 'GeneralInfoContainer', reducer });
const withSaga = injectSaga({ key: 'GeneralInfoContainer', saga });



export default compose(
  withSaga,
  withReducer,
  withConnect,
  withRouter,
)(GeneralInfoContainer);
