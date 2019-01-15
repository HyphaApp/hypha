import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';
import ListingItem from '@components/ListingItem';

import './style.scss';

export default class Listing extends React.Component {
    renderListItems() {
        if (this.props.isLoading) {
            return <ListingItem title={"Loading..."} />;
        } else if (this.props.isError) {
            return <ListingItem title={"Something went wrong. Please try again later."} />;
        } else if (this.props.items.length === 0) {
            return <ListingItem title={"No results found."} />;
        }

        const listItems = [];
        for (const item of this.props.items) {
            listItems.push(
                <ListingHeading key={`item-${item.id}`} title={item.title} count={item.subitems.length} />
            );

            const subitems = [];
            for (const subitem of item.subitems) {

                subitems.push(
                    <ListingItem key={`subitem-${subitem.id}`} title={subitem.title} />
                );
            }
            listItems.push(
                <ul key={`subitems-listing-${item.id}`}>
                    {subitems}
                </ul>
            );
        }
        return listItems;
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
    items: PropTypes.arrayOf(PropTypes.shape({
        title: PropTypes.string,
        id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
        subitems: PropTypes.arrayOf(PropTypes.shape({
            title: PropTypes.string,
            id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
        })),
    })),
    isLoading: PropTypes.bool,
    isError: PropTypes.bool,
};
