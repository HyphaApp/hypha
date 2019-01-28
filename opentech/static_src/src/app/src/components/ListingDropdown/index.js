import React from 'react';
import PropTypes from 'prop-types';
import smoothscroll from 'smoothscroll-polyfill';

export default class ListingDropdown extends React.Component {
    static propTypes = {
        listRef: PropTypes.object,
        groups: PropTypes.array,
        scrollOffset: PropTypes.number,
    }

    componentDidMount() {
        // polyfill element.scrollTo
        smoothscroll.polyfill();
    }

    handleChange(e) {
        const groupHeaderPosition = document.getElementById(e.target.value).offsetTop - this.props.scrollOffset;

        this.props.listRef.current.scrollTo({
            top: groupHeaderPosition
        })
    }

    renderListDropdown() {
        const { groups } = this.props;

        return (
            <form className="form form__select">
                <select onChange={(e) => this.handleChange(e)} aria-label="Jump to listing group">
                    {groups.map(group => {
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
