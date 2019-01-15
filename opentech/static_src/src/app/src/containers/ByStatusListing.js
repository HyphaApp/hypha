import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import Listing from '@components/Listing';
import {
    getCurrentRoundID,
    getCurrentRoundSubmissions,
    getSubmissionsByRoundErrorState,
    getSubmissionsByRoundLoadingState,
} from '@selectors/submissions';
import { setCurrentSubmissionRound, fetchSubmissionsByRound } from '@actions/submissions';


class ByStatusListing extends React.Component {
    componentDidMount() {
        const { roundId } = this.props;
        // Update items if round ID is defined.
        if (roundId !== null && roundId !== undefined) {
            this.props.loadSubmissions(roundId);
        }
    }

    componentDidUpdate(prevProps) {
        const { roundId } = this.props;
        // Update entries if round ID is changed or is not null.
        if (roundId !== null && roundId !== undefined && prevProps.roundId !== roundId) {
            this.props.loadSubmissions(roundId);
        }
    }

    render() {
        const { isLoading, isError } = this.props;
        return <Listing
                    isLoading={isLoading}
                    isError={isError}
                    items={this.props.items}
                    groupBy={'status'}
                    order={[
                        // TODO: Set the proper order of statuses.
                        'post_external_review_discussion',
                        'in_discussion',
                        'more_info',
                        'internal_review',
                        'post_review_discussion',
                        'post_review_more_info',
                        'accepted',
                        'rejected',
                    ]}
            />;
    }
}

const mapStateToProps = state => ({
    items: getCurrentRoundSubmissions(state),
    roundId: getCurrentRoundID(state),
    isError: getSubmissionsByRoundErrorState(state),
    isLoading: getSubmissionsByRoundLoadingState(state),
});

const mapDispatchToProps = dispatch => ({
    loadSubmissions: id => dispatch(fetchSubmissionsByRound(id)),
});

ByStatusListing.propTypes = {
    loadSubmissions: PropTypes.func,
    roundId: PropTypes.number,
};


export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ByStatusListing);
