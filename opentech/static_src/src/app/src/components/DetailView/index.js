import React from 'react';
import PropTypes from 'prop-types';
import './style.scss';

const DetailView = ({ children }) => (
    <div className="detail-view">
        {children}
    </div>
);

DetailView.propTypes = {
    children: PropTypes.node.isRequired,
};

export default DetailView;
