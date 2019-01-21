import React from 'react';
import PropTypes from 'prop-types';

import ListingGroup from '@components/ListingGroup';
import ListingItem from '@components/ListingItem';
import LoadingPanel from '@components/LoadingPanel';

import './style.scss';

export default class Listing extends React.Component {
    static propTypes = {
        items: PropTypes.array,
        activeItem: PropTypes.number,
        isLoading: PropTypes.bool,
        error: PropTypes.string,
        groupBy: PropTypes.string,
        order: PropTypes.arrayOf(PropTypes.string),
        onItemSelection: PropTypes.func,
    };

    state = {
        orderedItems: [],
    };

    componentDidMount() {
        this.orderItems();
    }

    componentDidUpdate(prevProps, prevState) {
        // Order items
        if (this.props.items !== prevProps.items) {
            this.orderItems();
        }

        const oldItem = prevProps.activeItem
        const newItem = this.props.activeItem

        // If we have never activated a submission, get the first item
        if ( !newItem && !oldItem ) {
            const firstGroup = this.state.orderedItems[0]
            if ( firstGroup && firstGroup.items[0] ) {
                this.setState({firstUpdate: false})
                this.props.onItemSelection(firstGroup.items[0].id)
            }
        }
    }

    renderListItems() {
        const { isLoading, error, items, onItemSelection, activeItem } = this.props;

        if (isLoading) {
            return (
                <div className="listing__list is-loading">
                    <LoadingPanel />
                </div>
            )
        } else if (error) {
            return (
                <div className="listing__list is-loading">
                    <p>Something went wrong. Please try again later.</p>
                    <p>{ error }</p>
                </div>
            )
        } else if (items.length === 0) {
            return (
                <div className="listing__list is-loading">
                    <p>No results found.</p>
                </div>
            )
        }

        return (
            <ul className="listing__list">
                {this.state.orderedItems.map(group => {
                    return (
                        <ListingGroup key={`listing-group-${group.name}`} item={group}>
                            {group.items.map(item => {
                                return <ListingItem
                                    selected={!!activeItem && activeItem===item.id}
                                    onClick={() => onItemSelection(item.id)}
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
        const leftOverKeys = Object.keys(groupedItems).filter(v => !order.includes(v));
        this.setState({
            orderedItems: order.concat(leftOverKeys).filter(key => groupedItems[key] ).map(key => ({
                name: key,
                items: groupedItems[key] || []
            })),
        });
    }

    render() {
        return (
            <div className="listing">
                <div className="listing__header"></div>
                {this.renderListItems()}
            </div>
        );
    }
}
