import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';

import {
    getCurrentRound,
    getSubmissionsByRoundError,
    getCurrentRoundSubmissions
} from '@selectors/submissions';


class GroupByStatusDetailView extends React.Component {
    static propTypes = {
        submissions: PropTypes.arrayOf(PropTypes.object),
        round: PropTypes.object,
        error: PropTypes.string,
    };

    render() {
        const listing = <ByStatusListing />;
        const { round, error, submissions } = this.props;
        const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
        const isEmpty = submissions.length === 0;

        return (
            <DetailView
                listing={listing}
                isLoading={isLoading}
                error={error}
                isEmpty={isEmpty}
            />
        );
    }
}

const mapStateToProps = state => ({
    round: getCurrentRound(state),
    error: getSubmissionsByRoundError(state),
    submissions: getCurrentRoundSubmissions(state),
})

export default connect(
    mapStateToProps,
)(GroupByStatusDetailView);
