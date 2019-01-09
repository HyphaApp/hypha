import React from 'react';
import { connect } from 'react-redux'

import SubmissionsByRoundList from '@components/SubmissionsByRoundList';


class SubmissionsByRoundContainer extends React.Component {
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
        items: state.submissions.items,
    }
}

const mapDispatchToProps = dispatch => {
    return {};
}


export default connect(
    mapStateToProps,
    mapDispatchToProps
)(SubmissionsByRoundContainer);
