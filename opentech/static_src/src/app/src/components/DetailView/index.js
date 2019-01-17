import React, { Component } from 'react'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { withWindowSizeListener } from 'react-window-size-listener';

import DisplayPanel from '@containers/DisplayPanel';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'
import { getCurrentSubmissionID } from '@selectors/submissions';

import './style.scss';

class DetailView extends Component {
    constructor() {
        super();
        this.state = {
            hasActiveApplication: false
        }
    }

    render() {
        const { listing, hasActiveApplication, windowSize: {windowWidth: width}} = this.props;
        const isMobile = width < 1024;

        if (isMobile) {
            return (
                <div className="detail-view">
                    <SlideInRight in={!hasActiveApplication}>
                        <DisplayPanel />
                    </SlideInRight>
                    <SlideOutLeft in={hasActiveApplication}>
                        {listing}
                    </SlideOutLeft>
                </div>
            )
        } else {
            return (
                <div className="detail-view">
                    {listing}
                    <DisplayPanel />
                </div>
            )
        }

    }
};

DetailView.propTypes = {
    listing: PropTypes.node.isRequired,
    hasActiveApplication: PropTypes.bool,
};

const mapStateToProps = state => ({
    hasActiveApplication: !!getCurrentSubmissionID(state),
});


export default connect(mapStateToProps)(withWindowSizeListener(DetailView));
