import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';
import ListingGroup from '@components/ListingGroup';
import ListingItem from '@components/ListingItem';

import './style.scss';

export default class Listing extends React.Component {
    state = { orderedItems: [] };

    componentDidUpdate(prevProps, prevState) {
        // Order items
        if (this.props.items !== prevProps.items) {
            this.orderItems();
        }

        // Update the first item.
        const getFirstItem = items => {
            for (const group of items) {
                for (const item of group.items) {
                    return item;
                }
            }
            return null;
        };

        const prevFirstItem = getFirstItem(prevState.orderedItems);
        const firstItem = getFirstItem(this.state.orderedItems);

        if (firstItem !== null && (prevFirstItem === null || firstItem.id !== prevFirstItem.id)) {
            this.props.updateFirstItem(firstItem.id);
        }
    }

    renderListItems() {
        const { isLoading, isError, items, onItemSelection } = this.props;

        if (isLoading) {
            return <p>Loading...</p>;
        } else if (isError) {
            return <p>Something went wrong. Please try again later.</p>;
        } else if (this.props.items.length === 0) {
            return <p>No results found.</p>;
        }

        return (
            <ul className="listing__list">
                {this.state.orderedItems.filter(v => v.items.length !== 0).map(v => {
                    return (
                        <ListingGroup key={`listing-group-${v.group}`} item={v}>
                            {v.items.map(item => {
                                return <ListingItem
                                    onClick={onItemSelection}
                                    key={`listing-item-${item.id}`}
                                    item={item}/>;
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

    orderItems() {
        const groupedItems = this.getGroupedItems();
        const { order = [] } = this.props;
        const orderedItems = [];
        const leftOverKeys = Object.keys(groupedItems).filter(v => !order.includes(v));
        this.setState({
            orderedItems: order.concat(leftOverKeys).map(key => ({
                group: key,
                items: groupedItems[key] || []
            })),
        });
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
    onItemSelection: PropTypes.func,
    updateFirstItem: PropTypes.func,
};
