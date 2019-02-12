import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';

import {
    getCurrentRound,
} from '@selectors/submissions';


class GroupByStatusDetailView extends React.Component {
    static propTypes = {
        submissions: PropTypes.arrayOf(PropTypes.object),
        round: PropTypes.object,
    };

    render() {
        const listing = <ByStatusListing />;
        const { round } = this.props;
        const isLoading = !round || (round && (round.isFetching || round.submissions.isFetching))
        return (
            <DetailView listing={listing} isLoading={isLoading} />
        );
    }
}

const mapStateToProps = state => ({
    round: getCurrentRound(state),
})

export default connect(
    mapStateToProps,
)(GroupByStatusDetailView);
