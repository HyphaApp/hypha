import React from 'react';
import PropTypes from 'prop-types';

import ListingHeading from '@components/ListingHeading';
import ListingItem from '@components/ListingItem';

import './style.scss';

export default class Listing extends React.Component {
    renderListItems() {
        const listItems = [];
        for (const item of this.props.items) {
            listItems.push(
                <ListingHeading key={`item-${item.id}`} title={item.title} count={item.subitems.length} />
            );

            const submissions = [];
            for (const subitem of item.subitems) {

                submissions.push(
                    <ListingItem key={`subitem-${subitem.id}`} title={subitem.title} />
                );
            }
            listItems.push(
                <ul key={`subitems-listing-${item.id}`}>
                    {submissions}
                </ul>
            );
        }
        return listItems;
    }

    render() {
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
};
