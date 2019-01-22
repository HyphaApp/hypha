import React from 'react';
import PropTypes from 'prop-types';

import LoadingPanel from '@components/LoadingPanel';

export default class NotesPanelItem extends React.Component {
    static propTypes = {
        children: PropTypes.node,
        isLoading: PropTypes.bool.isRequired,
        isErrored: PropTypes.bool.isRequired,
        handleRetry: PropTypes.func.isRequired,
    };

    render() {
        const { children, handleRetry, isErrored, isLoading } = this.props;

        if (isLoading) {
            return <LoadingPanel />;
        } else if (isErrored) {
            return <>
                <p><strong>Something went wrong!</strong>Sorry we couldn&rsquo;t load notes</p>
                <a onClick={handleRetry}>Refresh</a>.
            </>;
        } else if (children.length === 0) {
            return <p>There aren&rsquo;t any notes for this application yet.</p>;
        }

        return (
            <ul>
                {children}
            </ul>
        );
    }
}
