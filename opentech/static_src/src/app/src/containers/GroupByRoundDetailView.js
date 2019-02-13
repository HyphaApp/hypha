import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByRoundListing from '@containers/ByRoundListing';
import {
    getRoundsFetching,
    getRoundsErrored,
} from '@selectors/rounds';
import {
    getByGivenStatusesLoading,
    getByGivenStatusesError,
    getCurrentRoundSubmissions
} from '@selectors/submissions';

class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
        submissions: PropTypes.arrayOf(PropTypes.object),
        isLoading: PropTypes.bool,
        isErrored: PropTypes.bool,
    };

    render() {
        const listing = <ByRoundListing submissionStatuses={this.props.submissionStatuses} />;
        const { isLoading, isErrored, submissions } = this.props;
        const isEmpty = submissions.length === 0;

        return (
            <DetailView
                listing={listing}
                isLoading={isLoading}
                error={isErrored ? 'Fetching failed.' : undefined}
                isEmpty={isEmpty}
            />
        );
    }
}

const mapStateToProps = (state, ownProps) => ({
    isErrored: (
        getByGivenStatusesError(ownProps.submissionStatuses)(state) ||
        getRoundsErrored(state)
    ),
    isLoading: (
        getByGivenStatusesLoading(ownProps.submissionStatuses)(state) ||
        getRoundsFetching(state)
    ),
    submissions: getCurrentRoundSubmissions(state),
})

export default connect(
    mapStateToProps,
)(GroupByRoundDetailView);
