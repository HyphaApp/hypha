import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';
import ListingGroup from '@components/ListingGroup';
import ListingItem from '@components/ListingItem';

import './style.scss';

export default class Listing extends React.Component {
    renderListItems() {
        const { isLoading, isError, items } = this.props;

        if (isLoading) {
            return <p>Loading...</p>;
        } else if (isError) {
            return <p>Something went wrong. Please try again later.</p>;
        } else if (items.length === 0) {
            return <p>No results found.</p>;
        }

        return (
            <ul className="listing__list">
                {this.getOrderedItems().filter(v => v.items.length !== 0).map(v => {
                    return (
                        <ListingGroup key={`listing-group-${v.group}`} item={v}>
                            {v.items.map(item => {
                                return <ListingItem key={`listing-item-${item.id}`} item={item}/>;
                            })}
                        </ListingGroup>
                    );
                })}
            </ul>
        );
    }

    getGroupedItems() {
        const { groupBy, items } = this.props;

        return items.reduce((tmpItems, v) => {
            const groupByValue = v[groupBy];
            if (!(groupByValue in tmpItems)) {
                tmpItems[groupByValue] = [];
            }
            tmpItems[groupByValue].push({...v});
            return tmpItems;
        }, {});
    }

    getOrderedItems() {
        const groupedItems = this.getGroupedItems();
        const { order = [] } = this.props;
        const orderedItems = [];
        const leftOverKeys = Object.keys(groupedItems).filter(v => !order.includes(v));
        return order.concat(leftOverKeys).map(key => ({
            group: key,
            items: groupedItems[key] || []
        }));
    }

    render() {
        const { isLoading, isError } = this.props;
        return (
            <div className="listing">
                <div className="listing__header"></div>
                {this.renderListItems()}
            </div>
        );
    }
}

Listing.propTypes = {
    items: PropTypes.array,
    isLoading: PropTypes.bool,
    isError: PropTypes.bool,
    groupBy: PropTypes.string,
    order: PropTypes.arrayOf(PropTypes.string),
};
