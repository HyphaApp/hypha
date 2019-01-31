import React from 'react';
import PropTypes from 'prop-types';
import SwitcherApp from './SwitcherApp';
import { hot } from 'react-hot-loader';

import GroupByRoundDetailView from '@containers/GroupByRoundDetailView';


class SubmissionsByStatusApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        statuses: PropTypes.arrayOf(PropTypes.string),
    };

    render() {
        return <SwitcherApp
                detailComponent={<GroupByRoundDetailView submissionStatuses={this.props.statuses} />}
                switcherSelector={'submissions-by-status-app-react-switcher'}
                pageContent={this.props.pageContent} />;
    }
}

export default hot(module)(SubmissionsByStatusApp);
