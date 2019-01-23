import React from 'react';
import PropTypes from 'prop-types';

export default class ListingDropdown extends React.Component {
    static propTypes = {
        list: PropTypes.object,
        items: PropTypes.array,
    }

    handleChange(e) {
        const groupHeaderPosition = document.getElementById(e.target.value).offsetTop - 75;

        this.props.list.scrollTo({
            top: groupHeaderPosition
        })
    }

    renderListDropdown() {
        const { items } = this.props;

        return (
            <form className="form form__select">
                <select onChange={(e) => this.handleChange(e)} aria-label="Jump to listing group">
                    {items.map(group => {
                        return (
                            <option key={`listing-heading-${group.name}`} value={group.name}>{group.name}</option>
                        )
                    })}
                </select>
            </form>
        )
    }

    render() {
        return (
            <>
                {this.renderListDropdown()}
            </>
        )
    }
}
