import React from 'react'

import OTFLoadingIcon from '@components/OTFLoadingIcon'

import './styles.scss';

const InlineLoading = () => {
    return (
        <div className="loading-inline">
            <div className="loading-inline__icon">
                <OTFLoadingIcon />
            </div>
        </div>
    )
}

export default InlineLoading
