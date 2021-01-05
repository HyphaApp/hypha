import React from 'react';
import PropTypes from 'prop-types';
import SwitcherApp from './SwitcherApp';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux'

import GroupByRoundDetailView from '@containers/GroupByRoundDetailView';
import { setCurrentStatuses } from '@actions/submissions';
import { getCurrentStatusesSubmissions } from '@selectors/submissions';


class SubmissionsByStatusApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        statuses: PropTypes.arrayOf(PropTypes.string),
        setStatuses: PropTypes.func.isRequired,
        submissions: PropTypes.array
    };

    componentDidMount() {
        this.props.setStatuses(this.props.statuses);
    }

    onfilter = () => { 
        this.props.setStatuses(this.props.statuses);
    }

    render() {
        return <SwitcherApp
                detailComponent={<GroupByRoundDetailView submissions= {this.props.submissions}/>}
                switcherSelector={'submissions-by-status-app-react-switcher'}
                pageContent={this.props.pageContent}
                doNotRenderFilter={['status']}
                onFilter={this.onfilter} />;
    }
}

const mapStateToProps = (state, ownProps) => ({
    submissions: getCurrentStatusesSubmissions(state),
})

const mapDispatchToProps = dispatch => {
    return {
        setStatuses: (statuses) => {
          dispatch(setCurrentStatuses(statuses));
        },
    }
};


export default hot(module)(
    connect(mapStateToProps, mapDispatchToProps)(SubmissionsByStatusApp)
);
