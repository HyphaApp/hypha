import React from 'react';
import injectReducer from '@utils/injectReducer';
import injectSaga from '@utils/injectSaga';
import {withRouter} from 'react-router-dom';
import {connect} from 'react-redux';
import {bindActionCreators, compose} from 'redux';
import PropTypes from 'prop-types';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
import * as Selectors from './selectors';
import './styles.scss';
import {SidebarBlock} from '@components/SidebarBlock';
import LoadingPanel from '@components/LoadingPanel';
import Chip from '@material-ui/core/Chip';
import DoneIcon from '@material-ui/icons/Done';
import SvgIcon from '@material-ui/core/SvgIcon';

export class ScreeningStatusContainer extends React.PureComponent {

    componentDidMount() {
        document.addEventListener('keydown', this.keydownHandler);
    }

    componentDidUpdate(prevProps) {
        const {submissionID, allScreeningStatuses, submissionScreening, screeningStatuses, screeningInfo} = this.props;

        if (submissionID != prevProps.submissionID && !Object.keys(submissionScreening).length) {this.props.showLoading();}

        if (allScreeningStatuses !== prevProps.allScreeningStatuses) {
            this.props.setScreeningSuccess(allScreeningStatuses);
            screeningInfo.loading && screeningInfo.defaultSelectedValue && screeningInfo.selectedValues && this.props.hideLoading();
        }

        if (Object.keys(submissionScreening).length && prevProps.submissionScreening !== submissionScreening) {
            this.props.setVisibleSelected(submissionScreening.selectedReasons);
            this.props.setDefaultSelected(submissionScreening.selectedDefault);
            screeningInfo.loading && screeningStatuses && this.props.hideLoading();
        }
    }

    componentWillUnmount() {
        document.removeEventListener('keydown', this.keydownHandler);
    }

    updateDefaultValue = (submissionID, defaultOption) => () => {
        if (this.props.screeningInfo.defaultSelectedValue.id != defaultOption.id) {
            this.props.selectDefautValue(submissionID, defaultOption);
        }
    };

    keydownHandler = (event) => {
        if (event.ctrlKey && event.keyCode == 85) {
            event.preventDefault();
            this.props.screeningStatuses &&
      this.updateDefaultValue(this.props.submissionID, this.props.defaultOptions.yes)();
        }
        if (event.ctrlKey && event.keyCode == 68) {
            event.preventDefault();
            this.props.screeningStatuses &&
      this.updateDefaultValue(this.props.submissionID, this.props.defaultOptions.no)();
        }
    };

    renderScreeningReasons = () => {
        const {visibleOptions, selectVisibleOption, submissionID} = this.props;

        if (visibleOptions && visibleOptions.length) {
            return (<div className="screening-visible-options" >
                <h6 style={{fontWeight: '550', width: '100%'}}>Screening reasons</h6>
                {visibleOptions.map(option =>
                    <Chip
                        style={{margin: '0.3em'}}
                        label={option.title}
                        variant={!option.selected ? 'outlined' : 'default'}
                        key={option.id}
                        icon={option.selected ? <DoneIcon /> : null}
                        onClick={() => selectVisibleOption(submissionID, option)}>
                    </Chip>)
                }
            </div>
            );
        }
    };

    render() {
        const {
            screeningStatuses,
            submissionID,
            defaultOptions,
            screeningInfo
        } = this.props;

        if (screeningInfo.loading) {
            return <LoadingPanel />;
        }

        if (screeningStatuses && defaultOptions.yes && defaultOptions.no) {
            const defaultSelectedId = screeningInfo.defaultSelectedValue &&
      screeningInfo.defaultSelectedValue.id;
            return (
                <SidebarBlock title="Screening Decision" >
                    <div className="screening-status-box" style={{padding: '1rem'}}>
                        <div className="screening-default-options" >
                            <div
                                className={defaultSelectedId == defaultOptions.yes.id ?
                                    'screening-status-yes-disabled' :
                                    'screening-status-yes-enabled'
                                }
                                onClick={this.updateDefaultValue(submissionID, defaultOptions.yes)}
                            >
                                <SvgIcon
                                    className = { defaultSelectedId == defaultOptions.yes.id ? 'thumbs-up-color' : ''}
                                    style={{alignSelf: 'center'}}
                                >
                                    <path d="m1.75 23h2.5c.965 0 1.75-.785 1.75-1.75v-11.5c0-.965-.785-1.75-1.75-1.75h-2.5c-.965 0-1.75.785-1.75 1.75v11.5c0 .965.785 1.75 1.75 1.75z"></path><path d="m12.781.75c-1 0-1.5.5-1.5 3 0 2.376-2.301 4.288-3.781 5.273v12.388c1.601.741 4.806 1.839 9.781 1.839h1.6c1.95 0 3.61-1.4 3.94-3.32l1.12-6.5c.42-2.45-1.46-4.68-3.94-4.68h-4.72s.75-1.5.75-4c0-3-2.25-4-3.25-4z"></path>
                                </SvgIcon>
                                <div>{defaultOptions.yes.title}</div>
                            </div>
                            <div
                                className={defaultSelectedId == defaultOptions.no.id ?
                                    'screening-status-no-disabled' :
                                    'screening-status-no-enabled'
                                }
                                onClick={this.updateDefaultValue(submissionID, defaultOptions.no)}
                            >
                                <SvgIcon
                                    className = { defaultSelectedId == defaultOptions.no.id ? 'thumbs-down-color' : ''}
                                    style={{alignSelf: 'center'}}
                                >
                                    <path d="m22.25 1h-2.5c-.965 0-1.75.785-1.75 1.75v11.5c0 .965.785 1.75 1.75 1.75h2.5c.965 0 1.75-.785 1.75-1.75v-11.5c0-.965-.785-1.75-1.75-1.75z"></path><path d="m5.119.75c-1.95 0-3.61 1.4-3.94 3.32l-1.12 6.5c-.42 2.45 1.46 4.68 3.94 4.68h4.72s-.75 1.5-.75 4c0 3 2.25 4 3.25 4s1.5-.5 1.5-3c0-2.376 2.301-4.288 3.781-5.273v-12.388c-1.601-.741-4.806-1.839-9.781-1.839z"></path>
                                </SvgIcon>
                                <div>{defaultOptions.no.title}</div>
                            </div>
                        </div>
                        {this.renderScreeningReasons()}
                    </div>
                </SidebarBlock>);
        }
        return null;
    }
}

ScreeningStatusContainer.propTypes = {
    submission: PropTypes.object,
    selectDefautValue: PropTypes.func,
    defaultOptions: PropTypes.object,
    screeningInfo: PropTypes.object,
    visibleOptions: PropTypes.array,
    selectVisibleOption: PropTypes.func,
    submissionID: PropTypes.number,
    screeningStatuses: PropTypes.array,
    showLoading: PropTypes.func,
    setScreeningSuccess: PropTypes.func,
    setVisibleSelected: PropTypes.func,
    setDefaultSelected: PropTypes.func,
    hideLoading: PropTypes.func,
    allScreeningStatuses: PropTypes.array,
    submissionScreening: PropTypes.object
};


const mapStateToProps = state => ({
    screeningInfo: Selectors.selectScreeningInfo(state),
    screeningStatuses: Selectors.selectScreeningStatuses(state),
    defaultOptions: Selectors.selectDefaultOptions(state),
    visibleOptions: Selectors.selectVisibleOptions(state)
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators(
        {
            selectDefautValue: Actions.selectDefaultValueAction,
            selectVisibleOption: Actions.selectVisibleOptionAction,
            setScreeningSuccess: Actions.setScreeningSuccessAction,
            setVisibleSelected: Actions.setVisibleSelectedAction,
            setDefaultSelected: Actions.setDefaultSelectedAction,
            hideLoading: Actions.hideLoadingAction,
            showLoading: Actions.showLoadingAction
        },
        dispatch,
    );
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({key: 'ScreeningStatusContainer', reducer});
const withSaga = injectSaga({key: 'ScreeningStatusContainer', saga});


export default compose(
    withSaga,
    withReducer,
    withConnect,
    withRouter,
)(ScreeningStatusContainer);
