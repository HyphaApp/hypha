import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';


export default class ListingGroup extends React.Component {
    static propTypes = {
        children: PropTypes.arrayOf(PropTypes.node),
        item: PropTypes.shape({
            name: PropTypes.string,
        }),
        id: PropTypes.string,
    };

    render() {
        const {id, item, children} = this.props
        return (
            <li id={id}>
                <ListingHeading  title={item.name} count={children.length} />
                <ul>
                    {children}
                </ul>
            </li>
        );
    }
}
