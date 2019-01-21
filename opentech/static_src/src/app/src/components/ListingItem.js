import React from 'react';
import PropTypes from 'prop-types';


export default class ListingItem extends React.Component {
    render() {
        const { onClick, item, selected} = this.props;
        return (
            <li className={"listing__item " + (selected ? "is-active" : "")}>
                <a className="listing__link" onClick={onClick}>
                    {item.title}
                </a>
            </li>
        );
    }
}

ListingItem.propTypes = {
    item: PropTypes.shape({
        title: PropTypes.string,
    }),
    onClick: PropTypes.func,
    selected: PropTypes.bool,
};
