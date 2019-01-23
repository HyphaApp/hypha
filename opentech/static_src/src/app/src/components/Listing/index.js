import React from 'react';
import PropTypes from 'prop-types';

import LoadingPanel from '@components/LoadingPanel';

import './style.scss';

export default class Listing extends React.Component {
    static propTypes = {
        items: PropTypes.array,
        activeItem: PropTypes.number,
        isLoading: PropTypes.bool,
        isError: PropTypes.bool,
        error: PropTypes.string,
        groupBy: PropTypes.string,
        order: PropTypes.arrayOf(PropTypes.string),
        onItemSelection: PropTypes.func,
        shouldSelectFirst: PropTypes.bool,
        renderItem: PropTypes.func.isRequired,
        handleRetry: PropTypes.func,
    };

    static defaultProps = {
        shouldSelectFirst: true,
    }

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

    renderListItems() {
        const {
            isError,
            isLoading,
            items,
            renderItem,
        } = this.props;

        if (isLoading) {
            return (
                <div className="listing__list is-loading">
                    <LoadingPanel />
                </div>
            );
        } else if (isError) {
            return this.renderError();
        } else if (items.length === 0) {
            return (
                <div className="listing__list is-loading">
                    <p>No results found.</p>
                </div>
            );
        }

        return (
            <ul className="listing__list">
                {items.map(v => renderItem(v))}
            </ul>
        );
    }

    renderError = () => {
        const { handleRetry, error } = this.props;
        const retryButton = <a onClick={handleRetry}>Refresh</a>;
        return (
            <div className="listing__list is-loading">
                <p>Something went wrong. Please try again later.</p>
                {error && <p>{error}</p>}
                {handleRetry && retryButton}
            </div>
        );
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
