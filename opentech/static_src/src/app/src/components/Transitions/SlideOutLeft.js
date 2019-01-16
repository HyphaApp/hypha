import React from 'react'
import Transition from 'react-transition-group/Transition';

const SlideOutLeft = ({ children, in: inProp }) => {
    const duration = 250;

    const defaultStyle = {
        transition: `transform ${duration}ms ease-in-out`,
        transform: 'translate3d(0, 0, 0)',
        position: 'absolute',
        width: '100%'
    }

    const transitionStyles = {
        entering: { transform: 'translate3d(0, 0, 0)' },
        entered: { transform: 'translate3d(-100%, 0, 0)' },
        exiting: { transform: 'translate3d(-100%, 0, 0)' },
        exited: { transform: 'translate3d(0, 0, 0)' }
    };

    return (
        <Transition in={inProp} timeout={duration}>
            {(state) => (
                <div style={{ ...defaultStyle, ...transitionStyles[state] }}>
                    {children}
                </div>
            )}
        </Transition>
    )
}

export default SlideOutLeft
