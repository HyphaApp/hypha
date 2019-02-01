import React from 'react';
import PropTypes from 'prop-types';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux'

import SwitcherApp from './SwitcherApp';
import GroupByStatusDetailView from '@containers/GroupByStatusDetailView';
import { setCurrentSubmissionRound } from '@actions/submissions';


class SubmissionsByRoundApp extends React.Component {
    static propTypes = {
        roundID: PropTypes.number,
        setSubmissionRound: PropTypes.func,
        pageContent: PropTypes.node.isRequired,
    };

    componentDidMount() {
        this.props.setSubmissionRound(this.props.roundID);
    }

    render() {
        return <SwitcherApp
                detailComponent={<GroupByStatusDetailView />}
                switcherSelector={'submissions-by-round-app-react-switcher'}
                pageContent={this.props.pageContent} />;
    }
}

const mapDispatchToProps = dispatch => {
    return {
        setSubmissionRound: id => {
            dispatch(setCurrentSubmissionRound(id));
        },
    }
};

export default hot(module)(
    connect(null, mapDispatchToProps)(SubmissionsByRoundApp)
);
