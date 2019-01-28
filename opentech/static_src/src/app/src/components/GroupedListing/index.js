import React from 'react';
import PropTypes from 'prop-types';

import Listing from '@components/Listing';
import ListingGroup from '@components/ListingGroup';
import ListingItem from '@components/ListingItem';
import ListingDropdown from '@components/ListingDropdown';

import './styles.scss'

export default class GroupedListing extends React.Component {
    static propTypes = {
        items: PropTypes.array,
        activeItem: PropTypes.number,
        isLoading: PropTypes.bool,
        error: PropTypes.string,
        groupBy: PropTypes.string,
        order: PropTypes.arrayOf(PropTypes.string),
        onItemSelection: PropTypes.func,
        shouldSelectFirst: PropTypes.bool,
    };

    static defaultProps = {
        shouldSelectFirst: true,
    }


    state = {
        orderedItems: [],
    };

    constructor(props) {
        super(props);
        this.listRef = React.createRef();
    }

    componentDidMount() {
        this.orderItems();

        // get the height of the dropdown container
        this.dropdownContainerHeight = this.dropdownContainer.offsetHeight;
    }

    componentDidUpdate(prevProps, prevState) {
        // Order items
        if (this.props.items !== prevProps.items) {
            this.orderItems();
        }

        if ( this.props.shouldSelectFirst ){
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

    renderItem = group => {
        const { activeItem, onItemSelection } = this.props;
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
    }

    render() {
        const { isLoading, error } = this.props;
        const isError = Boolean(error);

        const passProps = {
            items: this.state.orderedItems,
            renderItem: this.renderItem,
            isLoading,
            isError,
            error
        };

        return  (
            <div className="grouped-listing">
                <div className="grouped-listing__dropdown" ref={(ref) => this.dropdownContainer = ref}>
                    {!error && !isLoading &&
                        <ListingDropdown
                            error={error}
                            isLoading={isLoading}
                            listRef={this.listRef}
                            groups={this.state.orderedItems}
                            scrollOffset={this.dropdownContainerHeight}
                        />
                    }
                </div>
                <Listing {...passProps} listRef={this.listRef} />
            </div>
        );
    }
}
