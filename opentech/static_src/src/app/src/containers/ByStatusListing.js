import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import Listing from '@components/Listing';
import {
    getCurrentRound,
    getCurrentRoundSubmissionsByStatus,
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
        return <Listing isLoading={isLoading} isError={isError} items={this.getListingItems()} />;
    }

    getListingItems() {
        return this.props.items.map(v => ({
            id: v.id,
            title: v.title,
            subitems: v.submissions.map(v => ({
                title: v.title,
                id: v.id,
            })),
        }));
    }
}

const mapStateToProps = state => ({
    items: getCurrentRoundSubmissionsByStatus(state),
    roundId: getCurrentRound(state),
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
