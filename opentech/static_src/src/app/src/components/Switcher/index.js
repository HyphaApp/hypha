import React from 'react'
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';

import ArrayIcon from 'images/icon-array.svg'
import GridIcon from 'images/icon-grid.svg';

import './styles.scss';

class Switcher extends React.Component {
    static propTypes = {
        handleOpen: PropTypes.func.isRequired,
        handleClose: PropTypes.func.isRequired,
        selector: PropTypes.string.isReqiured,
        open: PropTypes.bool,
    }

    constructor(props) {
        super(props);
        this.el = document.getElementById(props.selector);
    }

    render() {
        const { handleOpen, handleClose, open } = this.props;

        return ReactDOM.createPortal(
            <>
                <button className={`button button--switcher ${open ? 'is-active' : ''}`} onClick={handleOpen} aria-label="Show grid"><ArrayIcon /></button>
                <button className={`button button--switcher ${open ? '' : 'is-active'}`} onClick={handleClose} aria-label="Show table"><GridIcon /></button>
            </>,
            this.el,
        );
    }
}

export default Switcher
