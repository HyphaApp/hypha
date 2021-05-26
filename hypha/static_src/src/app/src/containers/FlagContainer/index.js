import React from 'react'
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
import "./style.scss";
import { SidebarBlock } from '@components/SidebarBlock'
import FlagIcon from '@material-ui/icons/Flag';
import LoadingPanel from '@components/LoadingPanel'

class FlagContainer extends React.PureComponent {

    constructor(props){
        super(props);
        this.props.initAction(
            this.props.type, 
            this.props.title, 
            this.props.APIPath
        )
        this.props.getSelectedFlag(this.props.type, this.props.selected)
    }

    render(){
        return (
            this.props.flagInfo[this.props.type] 
            && this.props.flagInfo[this.props.type].loading 
            ? <LoadingPanel /> :
            <div className="flag-block">
                <SidebarBlock title={this.props.title}>
                    <div className="status-actions">
                        <button 
                            className="button button--primary button--full-width flag-button"
                            onClick={() => this.props.flagInfo[this.props.type] && 
                                !this.props.flagInfo[this.props.type].isFlagClicked && this.props.setFlag(this.props.type, this.props.APIPath)}
                            style={ this.props.flagInfo[this.props.type] && 
                                this.props.flagInfo[this.props.type].isFlagClicked 
                                ? { opacity: '0.6', cursor: 'not-allowed'} : {opacity : '1'}}
                        >
                            <>
                                <span>{this.props.type === "staff" ? "Staff flag" : "Flag"}</span>
                                {
                                    this.props.flagInfo[this.props.type] 
                                    && this.props.flagInfo[this.props.type].isFlagged 
                                    && <FlagIcon style={{color : 'red', paddingLeft: '3px'}}/>
                                }
                            </>
                        </button>
                    </div>
                </SidebarBlock>
            </div>
        )
    }
}

FlagContainer.propTypes = {
    flagInfo: PropTypes.object,
    initAction: PropTypes.func,
    setFlag: PropTypes.func,
    type: PropTypes.string,
    title: PropTypes.string,
    APIPath: PropTypes.string,
    submissionID: PropTypes.number,
    getSelectedFlag: PropTypes.func,
    selected: PropTypes.bool
}

const mapStateToProps = state =>  ({
    flagInfo : Selectors.selectFlagContainerInfo(state),
});
  
  
function mapDispatchToProps(dispatch) {
    return bindActionCreators({
        initAction: Actions.initAction,
        setFlag: Actions.setFlagAction,
        getSelectedFlag: Actions.getSelectedFlagAction
    },
    dispatch,
    );
}
  
const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);
  
const withReducer = injectReducer({ key: 'FlagContainer', reducer });
const withSaga = injectSaga({ key: 'FlagContainer', saga });
  
  
export default compose(
withSaga,
withReducer,
withConnect,
withRouter,
)(FlagContainer);
