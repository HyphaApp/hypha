import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';

export default class ListingGroup extends React.Component {
    render() {
        return (
            <>
                <ListingHeading title={this.props.item} count={this.props.children.length} />
                <ul>
                    {this.props.children}
                </ul>
            </>
        );
    }
}

ListingGroup.propTypes = {
    item: PropTypes.object,
};
