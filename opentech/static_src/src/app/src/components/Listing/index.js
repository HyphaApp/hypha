import React from 'react';
import PropTypes from 'prop-types';

import LoadingPanel from '@components/LoadingPanel';
import EmptyPanel from '@components/EmptyPanel';

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
                <div className="listing__list">
                    <LoadingPanel />
                </div>
            );
        } else if (isError) {
            return this.renderError();
        } else if (items.length === 0) {
            return <EmptyPanel column={this.props.column} />;
        }

        return (
            <ul className={`listing__list listing__list--${column}`} ref={listRef}>
                {items.map(v => renderItem(v))}
            </ul>
        );
    }

    renderError = () => {
        const { handleRetry, error, column } = this.props;
        const retryButton = <a className="listing__help-link" onClick={handleRetry}>Refresh</a>;

        return (
            <div className={`listing__list listing__list--${column} is-blank`}>
                {error && <p>{error}</p>}

                {!handleRetry &&
                    <p>Something went wrong!</p>
                }

                {handleRetry && retryButton &&
                    <>
                        <div className="listing__blank-icon">
                            <SadNoteIcon  />
                        </div>
                        <p className="listing__help-text listing__help-text--standout">Something went wrong!</p>
                        <p className="listing__help-text">Sorry we couldn&apos;t load the notes</p>
                        {retryButton}
                    </>
                }
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
