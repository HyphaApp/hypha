import React from 'react';
import PropTypes from 'prop-types';

export default class ListingHeading extends React.Component {
    render() {
        return (
            <li className="listing__item listing__item--heading">
                <h5 className="listing__title">{this.props.title}</h5>
                <span className="listing__count">{this.props.count}</span>
            </li>
        );
    }
}

ListingHeading.propTypes = {
    title: PropTypes.string,
    count: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
    ]),
};
