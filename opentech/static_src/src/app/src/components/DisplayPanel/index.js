import React from 'react';
import ApplicationDisplay from '@components/ApplicationDisplay'
import Tabber from '@components/Tabber'
import './style.scss';

const DisplayPanel = () => (
    <div className="display-panel">
        <ApplicationDisplay />
        <Tabber />
    </div>
);

export default DisplayPanel;
