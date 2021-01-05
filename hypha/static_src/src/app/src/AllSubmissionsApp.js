import React from 'react';
import PropTypes from 'prop-types';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux'
import SwitcherApp from './SwitcherApp';
import GroupByRoundDetailView from '@containers/GroupByRoundDetailView';
import { setCurrentStatuses } from '@actions/submissions';
import {
    getSubmissionsForListing,
} from '@selectors/submissions';

class AllSubmissionsApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        setStatuses: PropTypes.func.isRequired,
        submissions: PropTypes.array,
        doNotRenderFilter: PropTypes.array
    };


    componentDidMount() {
        this.props.setStatuses([]);
    }

    onfilter = () => {
      this.props.setStatuses([])
    }

    render() {
        return (
            <SwitcherApp
                detailComponent={<GroupByRoundDetailView submissions= {this.props.submissions} groupBy="all"/>}
                switcherSelector={'submissions-all-react-app-switcher'}
                doNotRenderFilter={[]}
                pageContent={this.props.pageContent}
                onFilter={this.onfilter} />
        )
    }
}

const mapStateToProps = (state, ownProps) => ({
    submissions: getSubmissionsForListing(state),
})

const mapDispatchToProps = dispatch => {
    return {
        setStatuses: statuses => {dispatch(setCurrentStatuses(statuses));},
    }
};

export default hot(module)(
    connect(mapStateToProps, mapDispatchToProps)(AllSubmissionsApp)
);
