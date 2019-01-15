import React, {Component} from 'react';

export const Tab = ({name, children}) => <div>{children}</div>

class Tabber extends Component {
    constructor() {
        super();

        this.state = {
            activeTab: 0
        }
    }

    handleClick = (e) => {
        e.preventDefault();
        this.setState({
            activeTab: event.target.getAttribute('data-tab')
        })
    }

    render() {

        const { children, className } = this.props;
        const [ mainDisplay, ...other ] = children;

        return (
            <div className={className}>
                <div className="display-panel__header display-panel__header--spacer"></div>
                <div className="display-panel__header display-panel__links">
                    <a data-tab="0" onClick={this.handleClick} className="display-panel__link">{mainDisplay.props.name}</a>
                    {other.map((child, i) => <a data-tab={i + 1} onClick={this.handleClick} className="display-panel__link" key={child.props.name}>{child.props.name}</a>)}
                </div>
                <div className="display-panel__body">
                    {mainDisplay}
                </div>
                <div className="display-panel__body">
                    {other[0]}
                </div>
            </div>
        )
    }

}

export default Tabber;
