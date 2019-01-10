import React from 'react'
import ReactDOM from 'react-dom';
import ArrayIcon from 'images/icon-array.svg'
import GridIcon from 'images/icon-grid.svg';

import './styles.scss';

class Switcher extends React.Component {
    constructor(props) {
        super(props);
        this.el = document.getElementById(props.selector);
    }

    render() {
        const { handleOpen, handleClose, open } = this.props;

        return ReactDOM.createPortal(
            <>
                <button className={`button button--switcher ${open ? 'is-active' : ''}`} onClick={handleOpen}><ArrayIcon /></button>
                <button className={`button button--switcher ${open ? '' : 'is-active'}`} onClick={handleClose}><GridIcon /></button>
            </>,
            this.el,
        );
    }
}

export default Switcher
