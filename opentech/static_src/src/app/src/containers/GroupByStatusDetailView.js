import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';

import {
    getCurrentRound,
    getSubmissionsByRoundError,
} from '@selectors/submissions';


class GroupByStatusDetailView extends React.Component {
    static propTypes = {
        submissions: PropTypes.arrayOf(PropTypes.object),
        round: PropTypes.object,
        error: PropTypes.string,
    };

    render() {
        const listing = <ByStatusListing />;
        const { round, error } = this.props;
        const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
        return (
            <DetailView listing={listing} isLoading={isLoading} error={error} />
        );
    }
}

const mapStateToProps = state => ({
    round: getCurrentRound(state),
    error: getSubmissionsByRoundError(state),
})

export default connect(
    mapStateToProps,
)(GroupByStatusDetailView);
