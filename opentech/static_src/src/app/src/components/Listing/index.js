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
            return <ListingItem title={"Loading..."} />;
        } else if (isError) {
            return <ListingItem title={"Something went wrong. Please try again later."} />;
        } else if (items.length === 0) {
            return <ListingItem title={"No results found."} />;
        }

        return this.getOrderedItems().filter(v => v.items.length !== 0).map(v =>
            <ListingGroup key={`listing-group-${v.group}`} item={v.group}>
                {v.items.map(item =>
                    <ListingItem key={`listing-item-${item.id}`} title={item.title}/>
                )}
            </ListingGroup>
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
                <div className="listing__header">
                <form className="form form__select">
                    <select>
                        <option>Option 1</option>
                        <option>Option 2</option>
                        <option>Option 3</option>
                    </select>
                </form>
                </div>
                <ul className="listing__list">
                    {this.renderListItems()}
                </ul>
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
