import React, {Component} from 'react';
import PropTypes from 'prop-types';



export const Tab = ({button, children, handleClick}) => <div>{children}</div>
Tab.propTypes = {
    button: PropTypes.node,
    children: PropTypes.node,
    handleClick: PropTypes.func,
}

class Tabber extends Component {
    static propTypes = {
        children: PropTypes.arrayOf(PropTypes.element),
    }

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
                    {children.map((child, i) => {
                            return <a onClick={child.props.handleClick ? child.props.handleClick : () => this.handleClick(i)} className="display-panel__link" key={child.key}>{child.props.button}</a>
                        })
                    }
                </div>
                <div className="tabber-tab__active">
                    { children[this.state.activeTab] }
                </div>
            </div>
        )
    }

}

export default Tabber;
