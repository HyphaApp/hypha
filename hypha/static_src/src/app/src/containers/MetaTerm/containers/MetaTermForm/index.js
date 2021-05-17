import React from 'react'
import injectReducer from '@utils/injectReducer'
import injectSaga from '@utils/injectSaga'
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import { bindActionCreators, compose } from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './saga';
import * as Selectors from './selectors';
import { getCurrentSubmission } from '@selectors/submissions'
import LoadingPanel from '@components/LoadingPanel'
import MetaTermTreeView from './components/MetaTermTreeView'


class MetaTermForm extends React.PureComponent {

    componentDidMount(){
        this.props.initialize() // fetch all meta terms fields
        if("metaTerms" in this.props.submission) {
            this.props.setSelectedMetaTerms(this.props.submission.metaTerms.map(metaTerm => ''+metaTerm.id))
        }
    }

    render(){
        console.log(this.props.metaTermsInfo.selectedMetaTerms)
        return (
            this.props.metaTermsInfo.loading ? <LoadingPanel /> :
            <MetaTermTreeView 
              closeForm={this.props.closeForm}
              selectedMetaTerms={this.props.metaTermsInfo.selectedMetaTerms}
              metaTermsStructure={this.props.metaTermsInfo.metaTermsStructure}
              setSelectedMetaTerms={this.props.setSelectedMetaTerms}
              updateMetaTerms={() => this.props.updateMetaTerms(this.props.metaTermsInfo.selectedMetaTerms, this.props.submissionID)}
            />
        )
    }
}

MetaTermForm.propTypes = {
    initialize: PropTypes.func,
    metaTermsInfo: PropTypes.object,
    submissionID: PropTypes.number,
    closeForm: PropTypes.func,
    submission: PropTypes.object,
    setSelectedMetaTerms: PropTypes.func,
    updateMetaTerms: PropTypes.func
}

const mapStateToProps = state =>  ({
    metaTermsInfo : Selectors.selectMetaTermsInfo(state),
    submission: getCurrentSubmission(state)
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        initialize: Actions.initializeAction,
        setSelectedMetaTerms: Actions.setSelectedMetaTermsAction,
        updateMetaTerms: Actions.updateMetaTermsAction
    },
    dispatch,
);
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({ key: 'MetaTermForm', reducer });
const withSaga = injectSaga({ key: 'MetaTermForm', saga });


export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
)(MetaTermForm);
