import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';


export default class ListingGroup extends React.Component {
    static propTypes = {
        children: PropTypes.arrayOf(PropTypes.node),
        item: PropTypes.shape({
            name: PropTypes.string,
        }),
    };

    render() {
        const {item, children} = this.props
        return (
            <li>
                <ListingHeading title={item.name} count={children.length} />
                <ul>
                    {children}
                </ul>
            </li>
        );
    }
}
