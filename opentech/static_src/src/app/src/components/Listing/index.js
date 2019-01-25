import React from 'react';
import PropTypes from 'prop-types';

import LoadingPanel from '@components/LoadingPanel';

// import NoteIcon from 'images/note.svg';
import SadNoteIcon from 'images/sad-note.svg';

import './style.scss';

export default class Listing extends React.Component {
    static propTypes = {
        items: PropTypes.array.isRequired,
        isLoading: PropTypes.bool,
        isError: PropTypes.bool,
        error: PropTypes.string,
        groupBy: PropTypes.string,
        order: PropTypes.arrayOf(PropTypes.string),
        onItemSelection: PropTypes.func,
        renderItem: PropTypes.func.isRequired,
        handleRetry: PropTypes.func,
        listRef: PropTypes.object,
        column: PropTypes.string,
    };

    renderListItems() {
        const {
            isError,
            isLoading,
            items,
            renderItem,
            column,
            listRef,
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
            <ul className={`listing__list listing__list--${column}`} ref={listRef}>
                {items.map(v => renderItem(v))}
            </ul>
        );
    }

    renderError = () => {
        const { handleRetry, error } = this.props;
        const retryButton = <a onClick={handleRetry}>Refresh</a>;
        return (
            <div className="listing__list is-blank">
                <div className="listing__blank-icon">
                    <SadNoteIcon  />
                </div>
                <p>Something went wrong!</p>
                <p>Sorry we couldn&apos;t load the notes</p>
            <div className={`listing__list listing__list--${column} is-blank`}>
                {error && <p>{error}</p>}
                {handleRetry && retryButton}
            </div>
        );
    }

    render() {
        return (
            <div className="listing">
                {this.renderListItems()}
            </div>
        );
    }
}
