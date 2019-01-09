import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import SubmissionsByRoundList from '@components/SubmissionsByRoundList';
import { getCurrentRoundSubmissions } from '@selectors/submissions';
import { setCurrentSubmissionRound } from '@actions/submissions';


class SubmissionsByRoundContainer extends React.Component {
    constructor(props) {
        super(props);
        props.dispatch(setCurrentSubmissionRound(props.roundId));
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
        items: getCurrentRoundSubmissions(state),
    };
};

SubmissionsByRoundContainer.propTypes = {
    roundId: PropTypes.number,
};



export default connect(mapStateToProps)(SubmissionsByRoundContainer);
