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
} from '@selectors/submissions';

class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
        isLoading: PropTypes.bool,
        isErrored: PropTypes.bool,
    };

    render() {
        const listing = <ByRoundListing submissionStatuses={this.props.submissionStatuses} />;
        const { isLoading, isErrored } = this.props;

        return (
            <DetailView listing={listing} isLoading={isLoading} error={isErrored ? 'Fetching failed.' : undefined} />
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
})

export default connect(
    mapStateToProps,
)(GroupByRoundDetailView);
