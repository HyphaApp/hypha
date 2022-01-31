import React from 'react';
import PropTypes from 'prop-types';

import Listing from '@components/Listing';
import ListingGroup from '@components/ListingGroup';
import ListingItem from '@components/ListingItem';

import './styles.scss';

export default class GroupedListing extends React.Component {
    static propTypes = {
        items: PropTypes.array,
        activeItem: PropTypes.number,
        isLoading: PropTypes.bool,
        isErrored: PropTypes.bool,
        errorMessage: PropTypes.string,
        groupBy: PropTypes.string,
        order: PropTypes.arrayOf(PropTypes.shape({
            key: PropTypes.string.isRequired,
            display: PropTypes.string.isRequired,
            values: PropTypes.arrayOf(
                PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
            )
        })),
        onItemSelection: PropTypes.func,
        shouldSelectFirst: PropTypes.bool
    };

    static defaultProps = {
        shouldSelectFirst: true
    };

    state = {
        orderedItems: []
    };

    constructor(props) {
        super(props);
        this.listRef = React.createRef();
    }

    componentDidMount() {
        this.orderItems();
        document.addEventListener('keydown', this.keydownHandler);
    }

    componentWillUnmount() {
        document.removeEventListener('keydown', this.keydownHandler);
    }

    componentDidUpdate(prevProps, prevState) {
        // Order items
        if (this.props.items !== prevProps.items || this.props.order !== prevProps.order) {
            this.orderItems();
        }

        if (this.props.shouldSelectFirst && this.props.items.length) {
            const newItem = this.props.activeItem;
            // If we dont have an active item, then get one
            if (!newItem) {
                const firstGroup = this.state.orderedItems[0];
                if (firstGroup && firstGroup.items[0]) {
                    this.setState({firstUpdate: false});
                    this.props.onItemSelection(firstGroup.items[0].id);
                }
            }
        }
    }

    keydownHandler = (e) => {
        let orderedItems = [];
        let selected;

        // get ordered Ids
        this.state.orderedItems
            .map(group => group.items)
            .map(items => items.map(item => item.id))
            .map(orderedID => orderedItems = orderedItems.concat(orderedID));

        if (e.keyCode === 38 && e.ctrlKey) {
            selected = orderedItems[orderedItems.indexOf(this.props.activeItem) - 1];
        }
        else if (e.keyCode === 40 && e.ctrlKey) {
            selected = orderedItems[orderedItems.indexOf(this.props.activeItem) + 1];
        }

        if (selected == undefined) {return;}
        this.listRef.current.scrollTo({
            top: document.getElementById(selected).offsetTop
        });
        this.props.onItemSelection(selected);
        e.preventDefault();
    };

    getGroupedItems() {
        const {groupBy, items} = this.props;
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
        const {order = []} = this.props;
        const orderedItems = order.map(({key, display, values}) => ({
            name: display,
            key,
            items: values.reduce((acc, value) => acc.concat(groupedItems[value] || []), [])
        })).filter(({items}) => items.length !== 0);

        orderedItems.map(value => {
            value.items.sort((a, b) => a.lastUpdate > b.lastUpdate ? -1 : 1);
        });

        this.setState({orderedItems});
    }

    renderItem = group => {
        const {activeItem, onItemSelection} = this.props;
        return (
            <ListingGroup key={`listing-group-${group.key}`} id={group.key} item={group}>
                {group.items.map(item => {
                    return <ListingItem
                        selected={!!activeItem && activeItem === item.id}
                        onClick={() => onItemSelection(item.id)}
                        key={`listing-item-${item.id}`}
                        item={item}/>;
                })}
            </ListingGroup>
        );
    };

    render() {
        const {isLoading, isErrored, errorMessage} = this.props;
        const passProps = {
            items: this.state.orderedItems,
            renderItem: this.renderItem,
            isLoading,
            errorMessage,
            isErrored
        };


        return (
            <div className="grouped-listing">
                <Listing {...passProps} listRef={this.listRef} column="applications" />
            </div>
        );
    }
}
