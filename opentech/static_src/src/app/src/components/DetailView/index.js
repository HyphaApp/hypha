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

    isMobile = (width) => (width ? width : this.props.windowSize.windowWidth) < 1024

    render() {
        const { listing, hasActiveApplication } = this.props;

        if (this.isMobile()) {
            var activeDisplay;
            if (hasActiveApplication){
                activeDisplay = (
                    <SlideInRight key={"display"}>
                        <DisplayPanel />
                    </SlideInRight>
                )
            } else {
                activeDisplay = (
                    <SlideOutLeft key={"listing"}>
                        {listing}
                    </SlideOutLeft>
                )
            }

            return (
                <div className="detail-view">
                    { activeDisplay }
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
