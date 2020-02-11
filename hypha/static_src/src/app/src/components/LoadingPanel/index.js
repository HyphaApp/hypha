import React from 'react'

import OTFLoadingIcon from '@components/OTFLoadingIcon'

import './styles.scss';

const LoadingPanel = () => {
    return (
        <div className="loading-panel">
            <div className="loading-panel__text" >
                <h5>Loading...</h5>
            </div>
            <div className="loading-panel__icon" >
                <OTFLoadingIcon />
            </div>
        </div>
    )
}

export default LoadingPanel
