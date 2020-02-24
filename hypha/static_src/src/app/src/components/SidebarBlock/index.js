import React from 'react'
import PropTypes from 'prop-types'

import './styles.scss';

export const SidebarBlock = ({ title, children }) => {
    return (
        <div className="sidebar-block">
            {title && <h5>{title}</h5>}
            { children }
        </div>
    )
}

SidebarBlock.propTypes = {
    title: PropTypes.string,
    children: PropTypes.node,
}

export default SidebarBlock
