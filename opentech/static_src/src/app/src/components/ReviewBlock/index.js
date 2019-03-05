import React from 'react'
import PropTypes from 'prop-types'

import './styles.scss';

export const Opinion = ({ author, icon, opinion }) => (
    <li className="reviews-sidebar__item reviews-sidebar__item--decision">
        <div className="reviews-sidebar__name">
            <span>{author}</span><img src={icon} />
        </div>
        <div></div>
        <div className={`reviews-sidebar__outcome ${opinion.toLowerCase()}`}>{opinion}</div>
    </li>
)

Opinion.propTypes = {
    author: PropTypes.string,
    icon: PropTypes.string,
    opinion: PropTypes.string,
}

export const AssignedToReview = ({ author, icon }) => {
    return (
        <li className="reviews-sidebar__item">
            <div className="reviews-sidebar__name">{author}<img src={icon} /></div>
            <div>-</div>
            <div>-</div>
        </li>
    )
}

AssignedToReview.propTypes = {
    icon: PropTypes.string,
    author: PropTypes.string,
}

export const Review = ({ url, author, icon, score, recommendation, children }) => {
    const hasOpinions = children.length > 0;

    return (
        <>
            <li className="reviews-sidebar__item">
                <a target="_blank" rel="noopener noreferrer" href={url}>
                    <div className="reviews-sidebar__name">
                        {author}<img src={icon} />
                    </div>
                </a>
                <div>{recommendation.display}</div>
                <div>{parseFloat(score).toFixed(1)}</div>
            </li>

            {hasOpinions &&
                <ul className="reviews-sidebar__decision">
                    {children}
                </ul>
            }
        </>
    )
}

Review.propTypes = {
    author: PropTypes.string.isRequired,
    icon: PropTypes.string,
    score: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
    recommendation: PropTypes.shape({
        display: PropTypes.string.isRequired,
    }).isRequired,
    url: PropTypes.string.isRequired,
    children: PropTypes.node,
}

const ReviewBlock = ({ children, recommendation, score }) => {
    const renderTrafficLight = () => {
        const letter = recommendation.charAt(0)

        let modifierClass;
        if (recommendation === 'No') {
            modifierClass = 'red'
        } else if (recommendation === 'Yes') {
            modifierClass = 'green'
        } else if (recommendation === 'Maybe') {
            modifierClass = 'amber'
        }

        return <div aria-label="Traffic light score" className={`traffic-light traffic-light--${modifierClass}`}>{letter}</div>
    }

    return (
        <ul className="reviews-sidebar">
            {recommendation &&
                <li className="reviews-sidebar__item reviews-sidebar__item--header">
                    <div></div>
                    {recommendation &&
                        renderTrafficLight()
                    }
                    {!isNaN(parseFloat(score)) &&
                        <div>{parseFloat(score).toFixed(1)}</div>
                    }
                </li>
            }
            {children}
        </ul>
    )
}

ReviewBlock.propTypes = {
    children: PropTypes.node,
    score: PropTypes.number,
    recommendation: PropTypes.string,
}

export default ReviewBlock
