import React from 'react';
import PropTypes from 'prop-types';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux'

import Switcher from '@components/Switcher';
import GroupByStatusDetailView from '@containers/GroupByStatusDetailView';
import { setCurrentSubmissionRound } from '@actions/submissions';


class SubmissionsByRoundApp extends React.Component {
    static propTypes = {
        roundID: PropTypes.number,
        setSubmissionRound: PropTypes.func,
        pageContent: PropTypes.node.isRequired,
    };


    state = { detailOpened: false };

    componentDidMount() {
        this.props.setSubmissionRound(this.props.roundID);
    }

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
                <Switcher selector='submissions-by-round-app-react-switcher' open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpened &&
                    <GroupByStatusDetailView roundId={this.props.roundID} />
                }
            </>
        )
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
