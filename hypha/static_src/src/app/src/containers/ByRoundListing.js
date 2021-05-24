import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import GroupedListing from '@components/GroupedListing';
import {
    loadRounds,
    loadSubmissionsForCurrentStatus,
    setCurrentSubmission,
} from '@actions/submissions';
import {
    getRounds,
    getRoundsFetching,
    getRoundsErrored,
} from '@selectors/rounds';
import {
    getCurrentSubmissionID,
    getCurrentStatusesSubmissions,
    getSubmissionsForListing,
} from '@selectors/submissions';
import {
    getCurrentStatuses,
    getByStatusesLoading,
    getByStatusesError,
} from '@selectors/statuses';

import { SelectSelectedFilters } from '@containers/SubmissionFilters/selectors'

const loadData = props => {
    props.loadRounds()
    props.loadSubmissions()
}

class ByRoundListing extends React.Component {
    static propTypes = {
        statuses: PropTypes.arrayOf(PropTypes.string),
        loadSubmissions: PropTypes.func,
        submissions: PropTypes.arrayOf(PropTypes.object),
        isErrored: PropTypes.bool,
        setCurrentItem: PropTypes.func,
        activeSubmission: PropTypes.number,
        shouldSelectFirst: PropTypes.bool,
        rounds: PropTypes.object,
        isLoading: PropTypes.bool,
        errorMessage: PropTypes.string,
        filters: PropTypes.array,
        groupBy: PropTypes.string
    };

    componentDidMount() {
        if ( this.props.statuses || this.props.filters) {
            loadData(this.props)
        }
    }

    componentDidUpdate(prevProps) {
        const { statuses, groupBy } = this.props;
        
        if (!statuses.every(v => prevProps.statuses.includes(v)) 
            || !groupBy && !Object.keys(this.props.rounds).length 
            || this.props.filters != prevProps.filters) {
            loadData(this.props)
        }
    }

    prepareOrder = () => {
        const { isLoading, rounds, submissions } = this.props;
        if (isLoading || Object.entries(rounds).length === 0) {
            return []
        }
        return submissions.sort((a, b) => a.id - b.id )
                          .map(submission => submission.round)
                          .filter((round, index, arr) => round && arr.indexOf(round) === index)
                          .map((round, i) => ({
                              display: rounds[parseInt(round)].title,
                              key: `round-${round}`,
                              position: i,
                              values: [parseInt(round)],
                          }));
    }

    render() {
        const { isLoading, isErrored, submissions, setCurrentItem, activeSubmission, shouldSelectFirst, errorMessage } = this.props;
        const order = this.prepareOrder();
        return <GroupedListing
                isLoading={isLoading}
                isErrored={isErrored}
                errorMessage={errorMessage || 'Fetching failed.'}
                items={submissions || []}
                activeItem={activeSubmission}
                onItemSelection={setCurrentItem}
                shouldSelectFirst={shouldSelectFirst}
                groupBy={'round'}
                order={order}
            />;
    }
}

const mapStateToProps = (state, ownProps) => ({
    statuses: getCurrentStatuses(state),
    submissions: ownProps.groupBy ? getSubmissionsForListing(state) : getCurrentStatusesSubmissions(state),
    isErrored: getRoundsErrored(state) || getByStatusesError(state),
    isLoading: (
        getByStatusesLoading(state) ||
        getRoundsFetching(state)
    ),
    activeSubmission: getCurrentSubmissionID(state),
    rounds: getRounds(state),
    filters : SelectSelectedFilters(state)
})

const mapDispatchToProps = (dispatch) => ({
    loadSubmissions: () => dispatch(loadSubmissionsForCurrentStatus()),
    loadRounds: () => dispatch(loadRounds()),
    setCurrentItem: id => dispatch(setCurrentSubmission(id)),
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ByRoundListing);
