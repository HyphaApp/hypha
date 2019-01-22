import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission } from '@actions/submissions';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionErrorState,
    getSubmissionLoadingState,

} from '@selectors/submissions';

import CurrentSubmissionDisplay from '@containers/CurrentSubmissionDisplay'
import SubmissionNotesPanel from '@containers/SubmissionNotesPanel';
import Tabber, {Tab} from '@components/Tabber'
import './style.scss';


class DisplayPanel extends React.Component  {
    static propTypes = {
        submissionID: PropTypes.number,
        loadSubmission: PropTypes.func,
        isLoading: PropTypes.bool,
        isError: PropTypes.bool,
        clearSubmission: PropTypes.func.isRequired,
        windowSize: PropTypes.objectOf(PropTypes.number)
    };

    render() {
        const { windowSize: {windowWidth: width}, submissionID } = this.props;
        const { clearSubmission } = this.props;

        const isMobile = width < 1024;

        const submission = <CurrentSubmissionDisplay />

        let tabs = [
            <Tab button="Notes" key="note">
                <SubmissionNotesPanel submissionID={submissionID} />
            </Tab>,
            <Tab button="Status" key="status">
                <p>Status</p>
            </Tab>
        ]

        if ( isMobile ) {
            tabs = [
                <Tab button="Back" key="back" handleClick={ clearSubmission } />,
                <Tab button="Application" key="application">
                    { submission }
                </Tab>,
                ...tabs
            ]
        }

        return (
            <div className="display-panel">
                { !isMobile && (
                    <div className="display-panel__column">
                        <div className="display-panel__header display-panel__header--spacer"></div>
                        <div className="display-panel__body">
                            { submission }
                        </div>
                    </div>
                )}
                <div className="display-panel__column">
                    <div className="display-panel__body">
                        <Tabber>
                            { tabs }
                        </Tabber>
                    </div>
                </div>
            </div>

        )
    }
}

const mapStateToProps = state => ({
    isLoading: getSubmissionLoadingState(state),
    isError: getSubmissionErrorState(state),
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
});

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission
}


export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DisplayPanel));
