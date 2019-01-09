import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import SubmissionsByRoundList from '@components/SubmissionsByRoundList';
import { getCurrentRoundSubmissionsByStatus } from '@selectors/submissions';
import { setCurrentSubmissionRound, fetchSubmissionsByRound } from '@actions/submissions';


class SubmissionsByRoundContainer extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        this.props.setSubmissionRound(this.props.roundId);
        this.props.loadSubmissions(this.props.roundId);
    }

    render() {
        return (
            <>
                <SubmissionsByRoundList items={this.props.items} />
            </>
        );
    }
}


const mapStateToProps = state => {
    return {
        items: getCurrentRoundSubmissionsByStatus(state),
    };
};

const mapDispatchToProps = dispatch => {
    return {
        loadSubmissions: id => {
            dispatch(fetchSubmissionsByRound(id));
        },
        setSubmissionRound: id => {
            dispatch(setCurrentSubmissionRound(id));
        },
    }
};

SubmissionsByRoundContainer.propTypes = {
    roundId: PropTypes.number,
    loadSubmissions: PropTypes.func,
};



export default connect(mapStateToProps, mapDispatchToProps)(SubmissionsByRoundContainer);
