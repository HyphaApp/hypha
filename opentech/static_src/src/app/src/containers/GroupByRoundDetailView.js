import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByRoundListing from '@containers/ByRoundListing';
import {
    getRoundsFetching,
} from '@selectors/rounds';
import {
    getByGivenStatusesLoading,
} from '@selectors/submissions';

class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
        isLoading: PropTypes.bool,
    };

    render() {
        const listing = <ByRoundListing submissionStatuses={this.props.submissionStatuses} />;
        const { isLoading } = this.props;

        return (
            <DetailView listing={listing} isLoading={isLoading} />
        );
    }
}

const mapStateToProps = (state, ownProps) => ({
    isLoading: (
        getByGivenStatusesLoading(ownProps.submissionStatuses)(state) ||
        getRoundsFetching(state)
    ),
})

export default connect(
    mapStateToProps,
)(GroupByRoundDetailView);
