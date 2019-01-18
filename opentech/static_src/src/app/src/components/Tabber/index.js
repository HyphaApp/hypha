import React, {Component} from 'react';

export const Tab = ({button, children}) => <div>{children}</div>

class Tabber extends Component {
    constructor() {
        super();

        this.state = {
            activeTab: 0
        }
    }

    componentDidUpdate(prevProps, prevState) {
        const { children } = this.props;
        if ( !children[prevState.activeTab].props.children ) {
            this.setState({activeTab: children.findIndex(child => child.props.children)})
        }
    }

    handleClick = (child) => {
        this.setState({
            activeTab: child
        })
    }

    render() {
        const { children } = this.props;

        return (
            <div className="tabber">
                <div className="tabber__navigation">
                    {children.map((child, i) => <a onClick={() => this.handleClick(i)} className="display-panel__link" key={child.key}>{child.props.button}</a>)}
                </div>
                <div className="tabber-tab__active">
                    { children[this.state.activeTab] }
                </div>
            </div>
        )
    }

}

export default Tabber;
