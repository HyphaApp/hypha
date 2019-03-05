import React from 'react'
import PropTypes from 'prop-types'

import './styles.scss';

export const Opinion = ({ author, opinion }) => (
    <li className="reviews-sidebar__item reviews-sidebar__item--decision">
        <div className="reviews-sidebar__name">
            <span>{author}</span>
            {/* <img src={opinion.author.role.icon} /> */}
        </div>
        <div></div>
        <div className={`reviews-sidebar__outcome ${opinion.toLowerCase()}`}>{opinion}</div>
    </li>
)

Opinion.propTypes = {
    author: PropTypes.string,
    opinion: PropTypes.string,
}

export const AssignedToReview = ({ author }) => {
    return (
        <li className="reviews-sidebar__item">
            <div>{author}</div>
            <div>-</div>
            <div>-</div>
        </li>
    )
}

AssignedToReview.propTypes = {
    author: PropTypes.string,
}

export const Review = ({ url, author, score, recommendation, children }) => {
    const hasOpinions = children.length > 0;

    return (
        <>
            <li className="reviews-sidebar__item">
                <a target="_blank" rel="noopener noreferrer" href={url}>{author}</a>
                <div>{recommendation.display}</div>
                <div>{score}</div>
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
                        <div>{score}</div>
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
