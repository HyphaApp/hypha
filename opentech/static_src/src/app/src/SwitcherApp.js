import React from 'react';
import PropTypes from 'prop-types';

import Switcher from '@components/Switcher';
import MessagesContainer from '@containers/MessagesContainer'

export default class SwitcherApp extends React.Component {
    static propTypes = {
        pageContent: PropTypes.node.isRequired,
        detailComponent: PropTypes.node.isRequired,
        switcherSelector: PropTypes.string.isRequired,
    };

    componentDidMount() {
        const urlParams = new URLSearchParams(window.location.search);

        if (urlParams.has('submission')) {
            this.openDetail();
        }
    }

    state = { detailOpened: false };

    openDetail = () => {
        document.body.classList.add('app-open');
        this.setState(state => ({
            style: { ...state.style, display: 'none' } ,
            detailOpened: true,
        }));
    }

    closeDetail = () => {
        document.body.classList.remove('app-open');
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
                <MessagesContainer />
                <Switcher selector={this.props.switcherSelector} open={this.state.detailOpened} handleOpen={this.openDetail} handleClose={this.closeDetail} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpened && this.props.detailComponent}
            </>
        )
    }
}
