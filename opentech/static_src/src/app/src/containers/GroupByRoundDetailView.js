import React from 'react';
import PropTypes from 'prop-types';

import DetailView from '@components/DetailView';
import ByRoundListing from '@containers/ByRoundListing';

export default class GroupByRoundDetailView extends React.Component {
    static propTypes = {
        submissionStatuses: PropTypes.arrayOf(PropTypes.string),
    };

    render() {
        const listing = <ByRoundListing submissionStatuses={this.props.submissionStatuses} />;
        return (
            <DetailView listing={listing} />
        );
    }
}
