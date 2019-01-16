import React from 'react';
import PropTypes from 'prop-types';

import DisplayPanel from '@components/DisplayPanel';
import './style.scss';

const DetailView = ({ listing, display }) => (
    <div className="detail-view">
        {listing}
        <DisplayPanel />
    </div>
);

DetailView.propTypes = {
    listing: PropTypes.node.isRequired,
};

export default DetailView;
