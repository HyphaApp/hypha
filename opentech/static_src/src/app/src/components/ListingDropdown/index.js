import React from 'react';
import PropTypes from 'prop-types';

export default class ListingDropdown extends React.Component {
    static propTypes = {
        list: PropTypes.object,
        items: PropTypes.array,
        error: PropTypes.string,
        isLoading: PropTypes.bool,
    }

    handleChange(e) {
        const groupHeaderPosition = document.getElementById(e.target.value).offsetTop - 75;

        this.props.list.scrollTo({
            top: groupHeaderPosition
        })
    }

    renderListDropdown() {
        const { isLoading, error, items } = this.props;

        if (isLoading || error) {
            return;
        }

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
