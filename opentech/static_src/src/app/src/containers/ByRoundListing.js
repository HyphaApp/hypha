import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import GroupedListing from '@components/GroupedListing';
import {
    loadRounds,
    loadSubmissionsOfStatuses,
    setCurrentSubmission,
} from '@actions/submissions';
import {
    getRounds,
    getRoundsFetching,
    getRoundsErrored,
} from '@selectors/rounds';
import {
    getSubmissionsByGivenStatuses,
    getCurrentSubmissionID,
    getByGivenStatusesError,
    getByGivenStatusesLoading,
} from '@selectors/submissions';


const loadData = props => {
    props.loadRounds()
    props.loadSubmissions()
}

class ByRoundListing extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
        loadSubmissions: PropTypes.func,
        submissions: PropTypes.arrayOf(PropTypes.object),
        isErrored: PropTypes.bool,
        setCurrentItem: PropTypes.func,
        activeSubmission: PropTypes.number,
        shouldSelectFirst: PropTypes.bool,
        rounds: PropTypes.array,
        isLoading: PropTypes.bool,
        errorMessage: PropTypes.string,
    };

    componentDidMount() {
        // Update items if round ID is defined.
        if ( this.props.submissionStatuses ) {
            loadData(this.props)
        }
    }

    componentDidUpdate(prevProps) {
        const { submissionStatuses } = this.props;
        if (!submissionStatuses.every(v => prevProps.submissionStatuses.includes(v))) {
            loadData(this.props)
        }
    }

    prepareOrder = () => {
        const { isLoading, rounds, submissions } = this.props;
        if (isLoading)
            return []
        return submissions.map(submission => submission.round)
                          .filter((round, index, arr) => arr.indexOf(round) === index)
                          .map((round, i) => ({
                              display: rounds[parseInt(round)].title,
                              key: `round-${round}`,
                              position: i,
                              values: [round],
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
    submissions: getSubmissionsByGivenStatuses(ownProps.submissionStatuses)(state),
    isErrored: getRoundsErrored(state),
    errorMessage: getByGivenStatusesError(ownProps.submissionStatuses)(state),
    isLoading: (
        getByGivenStatusesLoading(ownProps.submissionStatuses)(state) ||
        getRoundsFetching(state)
    ),
    activeSubmission: getCurrentSubmissionID(state),
    rounds: getRounds(state),
})

const mapDispatchToProps = (dispatch, ownProps) => ({
    loadSubmissions: () => dispatch(loadSubmissionsOfStatuses(ownProps.submissionStatuses)),
    loadRounds: () => dispatch(loadRounds()),
    setCurrentItem: id => dispatch(setCurrentSubmission(id)),
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ByRoundListing);
