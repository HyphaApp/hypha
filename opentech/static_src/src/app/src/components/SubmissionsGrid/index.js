import React from 'react';
import PropTypes from 'prop-types';
import './style.scss';

const SubmissionsGrid = ({ children }) => (
    <div className="submissions-grid">
        {children}
    </div>
);

SubmissionsGrid.propTypes = {
    children: PropTypes.node.isRequired,
};

export default SubmissionsGrid;
