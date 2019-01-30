import React from 'react';
import PropTypes from 'prop-types';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux'

import GroupByRoundDetailView from '@containers/GroupByRoundDetailView';
import Switcher from '@components/Switcher';


class SubmissionsByStatusApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        statuses: PropTypes.arrayOf(PropTypes.string),
    };


    state = { detailOpened: false };

    openDetail = () => {
        this.setState(state => ({
            style: { ...state.style, display: 'none' } ,
            detailOpened: true,
        }));
    }

    closeDetail = () => {
        this.setState(state => {
            const newStyle = { ...state.style };
            delete newStyle.display;
            return {
                style: newStyle,
                detailOpened: false,
            };
        });
    }

    render() {
        return (
            <>
                <Switcher selector='submissions-by-status-app-react-switcher' open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpened &&
                    <GroupByRoundDetailView submissionStatuses={this.props.statuses} />
                }
            </>
        )
    }
}

export default hot(module)(
    connect(null, null)(SubmissionsByStatusApp)
);
