import React from 'react';
import PropTypes from 'prop-types';
import './ResizablePanels.scss';

class ResizablePanels extends React.Component {
    eventHandler = null;

    state = {
        isDragging: false,
        panels: this.props.panels
    };

    componentDidMount() {
        localStorage.getItem(this.props.panelType) &&
        this.setState({
            panels: localStorage.getItem(this.props.panelType).split(',').map(i => Number(i))
        });

        this.nv.addEventListener('mousemove', this.resizePanel);
        this.nv.addEventListener('mouseup', this.stopResize);
        this.nv.addEventListener('mouseleave', this.stopResize);
    }

    componentWillUnmount() {
        this.nv.removeEventListener('mousemove', this.resizePanel);
        this.nv.removeEventListener('mouseup', this.stopResize);
        this.nv.removeEventListener('mouseleave', this.stopResize);
    }

    startResize = (event, index) => {
        this.setState({
            isDragging: true,
            currentPanel: index,
            initialPos: event.clientX
        });
    };

    stopResize = () => {
        if (this.state.isDragging) {
            this.setState(({panels, currentPanel, delta}) => ({
                isDragging: false,
                panels: {
                    ...panels,
                    [currentPanel]: (((panels[currentPanel] * this.nv.clientWidth) / 100 || 0) - delta) * 100 / this.nv.clientWidth,
                    [currentPanel - 1]: (((panels[currentPanel - 1] * this.nv.clientWidth) / 100 || 0) + delta) * 100 / this.nv.clientWidth
                },
                delta: 0,
                currentPanel: null
            }));
            localStorage.setItem(this.props.panelType, [this.state.panels[0].toFixed(4), this.state.panels[1].toFixed(4)]);
        }
    };

    resizePanel = (event) => {
        if (this.state.isDragging) {
            const delta = event.clientX - this.state.initialPos;
            this.setState({
                delta: delta
            });
        }
    };

    render() {
        const rest = this.props.children.slice(1);
        return (
            <div ref={elem => this.nv = elem} className="panel-container" onMouseUp={() => this.stopResize()} style={{width: 'inherit'}}>
                <div className="panel" style={{width: `calc(100% - ${this.state.panels[1]}%`}}>
                    {this.props.children[0]}
                </div>
                {[].concat(...rest.map((child, i) => {
                    return [
                        <div onMouseDown={(e) => this.startResize(e, i + 1)}
                            key={'resizer_' + i}
                            style={this.state.currentPanel === i + 1 ? {left: this.state.delta} : {}}
                            className="resizer"></div>,
                        <div key={'panel_' + i} className="panel" style={{width: `${this.state.panels[i + 1]}%`}}>
                            {child}
                        </div>
                    ];
                }))}
            </div>
        );
    }
}

ResizablePanels.propTypes = {
    children: PropTypes.array,
    panelType: PropTypes.string,
    panels: PropTypes.array
};

export default ResizablePanels;
