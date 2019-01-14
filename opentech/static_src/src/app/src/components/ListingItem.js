import React from 'react';
import PropTypes from 'prop-types';


export default class ListingItem extends React.Component {
    render() {
        return (
            <li className="listing__item">
                <a className="listing__link">{this.props.title}</a>
            </li>
        );
    }
}

ListingItem.propTypes = {
    title: PropTypes.string,
};
