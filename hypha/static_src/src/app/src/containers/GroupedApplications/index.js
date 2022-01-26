import React from 'react';
import PropTypes from 'prop-types';
import {hot, setConfig} from 'react-hot-loader';
import {connect} from 'react-redux';
import {withRouter} from 'react-router-dom';
import injectReducer from '@utils/injectReducer';
import injectSaga from '@utils/injectSaga';
import {bindActionCreators, compose} from 'redux';
import * as Actions from './actions';
import reducer from './reducer';
import saga from './sagas';
import * as Selectors from './selectors';
import './styles.scss';
import LoadingPanel from '@components/LoadingPanel';

setConfig({showReactDomPatchNotification: false});

class GroupedApplications extends React.Component {
    static propTypes = {
        searchParam: PropTypes.string,
        initializeAction: PropTypes.func,
        groupedApplications: PropTypes.object
    };

    componentDidMount() {
        if (!this.props.searchParam) {
            window.location = '/apply/submissions/';
        }
        this.props.initializeAction(this.props.searchParam);
    }

    render() {
        return (
            this.props.groupedApplications.loading
                ?
                <LoadingPanel />
                :
                <div style={{marginTop: '35px'}}>
                    <ol style={{padding: '5px'}}>
                        {this.props.groupedApplications.applications.map((result) => {
                            return (
                                <li key={result.id}>
                                    <div>
                                        <a href={`/apply/submissions/${result.id}`} ><h5>{result.title}</h5></a>
                                        {result.summary.replace(/<[^>]+>/g, '') && <p dangerouslySetInnerHTML={{__html: result.summary}}/> }
                                    </div>
                                </li>
                            );
                        }
                        )}
                    </ol>
                </div>
        );
    }
}

const mapStateToProps = state => ({
    groupedApplications: Selectors.SelectGroupedApplicationsInfo(state),
    searchParam: state.router.location.search
});


function mapDispatchToProps(dispatch) {
    return bindActionCreators(
        {
            initializeAction: Actions.initializeAction
        },
        dispatch,
    );
}

const withConnect = connect(
    mapStateToProps,
    mapDispatchToProps,
);

const withReducer = injectReducer({key: 'GroupedApplications', reducer});
const withSaga = injectSaga({key: 'GroupedApplications', saga});

export default hot(module)(
    compose(
        withSaga,
        withReducer,
        withConnect,
        withRouter,
    )(GroupedApplications)
);
