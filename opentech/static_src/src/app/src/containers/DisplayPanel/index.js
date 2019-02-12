import React from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import { clearCurrentSubmission } from '@actions/submissions';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
} from '@selectors/submissions';

import CurrentSubmissionDisplay from '@containers/CurrentSubmissionDisplay'
import AddNoteForm from '@containers/AddNoteForm';
import NoteListing from '@containers/NoteListing';
import StatusActions from '@containers/StatusActions';
import Tabber, {Tab} from '@components/Tabber'
import './style.scss';

class DisplayPanel extends React.Component  {
    static propTypes = {
        submissionID: PropTypes.number,
        loadSubmission: PropTypes.func,
        clearSubmission: PropTypes.func.isRequired,
        windowSize: PropTypes.objectOf(PropTypes.number)
    };

    render() {
        const { windowSize: {windowWidth: width}, submissionID } = this.props;
        const { clearSubmission } = this.props;

        const isMobile = width < 1024;
        const submissionLink = "/apply/submissions/" + submissionID + "/";

        const submission = <CurrentSubmissionDisplay />

        let tabs = [
            <Tab button="Notes" key="note">
                <NoteListing submissionID={submissionID} />
                <AddNoteForm submissionID={submissionID} />
            </Tab>,
            <Tab button="Status" key="status">
                <StatusActions submissionID={submissionID} />
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
                        <div className="display-panel__body display-panel__body--center">
                            <a target="_blank" rel="noopener noreferrer" href={ submissionLink }>Open in new tab</a>
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
    submissionID: getCurrentSubmissionID(state),
    submission: getCurrentSubmission(state),
});

const mapDispatchToProps = {
    clearSubmission: clearCurrentSubmission
}

export default connect(mapStateToProps, mapDispatchToProps)(withWindowSizeListener(DisplayPanel));
