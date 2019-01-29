import React from 'react';
import PropTypes from 'prop-types';

export default class ListingHeading extends React.Component {
    render() {
        const parsedTitle = this.props.title.split(' ').join('-').toLowerCase();
        return (
            <div className="listing__item listing__item--heading" id={parsedTitle}>
                <h5 className="listing__title">{this.props.title}</h5>
                <span className="listing__count">{this.props.count}</span>
            </div>
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
