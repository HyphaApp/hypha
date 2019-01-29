import React from 'react';

import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';

export default class GroupByStatusDetailView extends React.Component {
    render() {
        const listing = <ByStatusListing />;
        return (
            <DetailView listing={listing} />
        );
    }
}
