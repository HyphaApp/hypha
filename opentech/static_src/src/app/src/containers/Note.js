import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import moment from 'moment';

import { getNoteOfID } from '@selectors/notes';

class Note extends React.Component {
    static propTypes = {
        note: PropTypes.shape({
            user: PropTypes.string,
            timestamp: PropTypes.string,
            message: PropTypes.string,
        }),
    };

    render() {
        const { note } = this.props;

        return (
            <div>
                <div style={{fontWeight: 'bold'}}>{note.user} - {moment(note.timestamp).format('ll')}</div>
                <div>{note.message}</div>
            </div>
        );
    }

}

const mapStateToProps = (state, ownProps) => ({
    note: getNoteOfID(ownProps.noteID)(state),
});

export default connect(mapStateToProps)(Note);
