import React from 'react';
// import {createStore} from 'redux';
import injectReducer from '@utils/injectReducer'
import injectSaga from '@utils/injectSaga'
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import { bindActionCreators, compose } from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
// import App from "./app"
import * as Selectors from './selectors';
import "./styles.scss";
import FormContainer from '@common/containers/FormContainer';
import LoadingPanel from '@components/LoadingPanel'
import { toggleReviewFormAction } from '../../redux/actions/submissions'


class ReviewFormContainer extends React.PureComponent {

  componentDidMount(){
    this.props.initializeAction(this.props.submissionID, this.props.reviewId ? this.props.reviewId : null)
    }

  getMetaFields(){

   let metaFieldsActions = [{
        text: "back",
        type: "secondary",
        callback: () => this.props.toggleReviewForm(false)
        }] ;

    if(this.props.formData.saveAsDraft){
      metaFieldsActions.push({
        text: "Update Draft",
        type: "secondary",
        callback: values => {
          let newValues = {...values, is_draft: true} 
          this.props.submitReview(newValues, this.props.submissionID)
             }  })
    }else if(!this.props.reviewId){
      metaFieldsActions.push({
        text: "Save Draft",
        type: "secondary",
        callback: values => {
          let newValues = {...values, is_draft: true}
          this.props.submitReview(newValues, this.props.submissionID)
        }
       })
    }

    if(this.props.reviewId){
      metaFieldsActions.push({
          text: "Update",
          type: "primary",
          callback: values => this.props.updateReview(values,this.props.submissionID, this.props.reviewId)
        })
      metaFieldsActions.push({
          text: "Delete",
          type: "warning",
          callback: () => this.props.deleteReview(this.props.reviewId, this.props.submissionID)
        })
    }
    else{
      metaFieldsActions.push({
          text: "Create",
          type: "primary",
          callback: values => this.props.submitReview(values, this.props.submissionID)
        })
    }


    
    return {
      fields: this.props.formData.metaStructure,
      actions: metaFieldsActions,
      initialValues: this.props.formData.initialValues
    }
  }

  render() {
      return <div 
      className={"container"}> 
      {this.props.reviewId ? <h3>Update Review</h3> : <h3>Create Review</h3> }
      {this.props.formData.loading ? <LoadingPanel /> : <> 
        <FormContainer metadata={this.getMetaFields()} formId={"myIntialForm"} />
      </>}
    </div>
  }
}

ReviewFormContainer.propTypes = {
  formData: PropTypes.object,
  initializeAction: PropTypes.func,
  submitReview: PropTypes.func,
  deleteReview: PropTypes.func,
  updateReview: PropTypes.func,
  toggleReviewForm: PropTypes.func,
  toggleSaveDraft: PropTypes.func,
  submissionID: PropTypes.number,
  reviewId: PropTypes.number,

}


const mapStateToProps = state =>  ({
    formData: Selectors.selectFieldsInfo(state),
  });


function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      initializeAction: Actions.initializeAction,
      submitReview: Actions.submitReviewAction,
      deleteReview: Actions.deleteReviewAction,
      updateReview: Actions.updateReviewAction,
      toggleReviewForm: toggleReviewFormAction,
      toggleSaveDraft: Actions.toggleSaveDraftAction
    },
    dispatch,
  );
}

const withConnect = connect(
  mapStateToProps,
  mapDispatchToProps,
);

const withReducer = injectReducer({ key: 'ReviewFormContainer', reducer });
const withSaga = injectSaga({ key: 'ReviewFormContainer', saga });



export default compose(
  withSaga,
  withReducer,
  withConnect,
  withRouter,
)(ReviewFormContainer);
