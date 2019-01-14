import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import DisplayPanel from '@components/DisplayPanel';
import DetailView from '@components/DetailView';
import ByStatusListing from '@containers/ByStatusListing';
import { setCurrentSubmissionRound } from '@actions/submissions';

class GroupByStatusDetailView extends React.Component {
    componentWillMount() {
        this.props.setSubmissionRound(this.props.roundId);
    }

    render() {
        const passProps = {
            listing: <ByStatusListing />,
            display: <DisplayPanel />,
        };
        return (
            <DetailView {...passProps} />
        );
    }
}

GroupByStatusDetailView.propTypes = {
    roundId: PropTypes.number,
};

const mapDispatchToProps = dispatch => {
    return {
        setSubmissionRound: id => {
            dispatch(setCurrentSubmissionRound(id));
        },
    }
};

export default connect(null, mapDispatchToProps)(GroupByStatusDetailView);
