import React, { Component } from 'react'
import PropTypes from 'prop-types';

import DisplayPanelContainer from '@containers/DisplayPanelContainer';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'

import './style.scss';

class DetailView extends Component {
    constructor() {
        super();
        this.state = {
            width: window.innerWidth,
            hasActiveApplication: false
        }
    }

    componentWillMount() {
        window.addEventListener('resize', this.handleWindowSizeChange.bind(this));
    }

    componentWillUnmount() {
        window.removeEventListener('resize', this.handleWindowSizeChange.bind(this));
    }

    handleWindowSizeChange = () => {
        this.setState({
            width: window.innerWidth
        })
    }

    render() {
        const { listing } = this.props;
        const { width, hasActiveApplication } = this.state;
        const isMobile = width < 1024;

        if (isMobile) {
            return (
                <div className="detail-view">
                    <SlideInRight in={!hasActiveApplication}>
                        <DisplayPanelContainer />
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
                    <DisplayPanelContainer />
                </div>
            )
        }

    }
};

DetailView.propTypes = {
    listing: PropTypes.node.isRequired,
};

export default DetailView;

