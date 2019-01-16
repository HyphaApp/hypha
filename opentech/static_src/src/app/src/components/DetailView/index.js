import React, { Component } from 'react'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';

import DisplayPanel from '@containers/DisplayPanel';
import SlideInRight from '@components/Transitions/SlideInRight'
import SlideOutLeft from '@components/Transitions/SlideOutLeft'
import { getCurrentSubmissionID } from '@selectors/submissions';

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
        });
    }

    render() {
        const { listing, hasActiveApplication } = this.props;
        const { width  } = this.state;
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


export default connect(mapStateToProps)(DetailView);

