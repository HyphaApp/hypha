import React from 'react';
import PropTypes from 'prop-types';
import './style.scss';

const DetailView = ({ listing, display }) => (
    <div className="detail-view">
        {listing}
        {display}
    </div>
);

DetailView.propTypes = {
    listing: PropTypes.node.isRequired,
    display: PropTypes.node.isRequired,
};

export default DetailView;
