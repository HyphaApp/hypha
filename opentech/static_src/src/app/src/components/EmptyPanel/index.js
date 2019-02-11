import React from 'react'
import PropTypes from 'prop-types';

import NoteIcon from 'images/note.svg';

export default class EmptyPanel extends React.Component {
    static propTypes = {
        column: PropTypes.string,
    }

    render() {
        const { column } = this.props;

        return (
            <div className={`listing__list listing__list--${column} is-blank`}>
                {column === 'notes' &&
                    <>
                        <div className="listing__blank-icon">
                            <NoteIcon />
                        </div>
                        <p className="listing__help-text listing__help-text--standout">
                            There aren&apos;t any notes<br /> for this appication yet&hellip;
                        </p>
                    </>
                }

                {column === 'applications' &&
                    <p>No results found.</p>
                }
            </div>
        )
    }
}
