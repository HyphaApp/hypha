import React from 'react'
import PropTypes from 'prop-types'

import './styles.scss';

const Opinion = ({ author, opinion }) => (
    <li className="reviews-sidebar__item reviews-sidebar__item--decision">
        <div className="reviews-sidebar__name">
            <span>{author}</span>
            {/* <img src={opinion.author.role.icon} /> */}
        </div>
        <div></div>
        <div className={`reviews-sidebar__outcome ${opinion.opinion.toLowerCase()}`}>{opinion.opinion}</div>
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

export const Review = ({ url, author, score, recommendation, opinions }) => {
    const hasOpinions = opinions.length > 0;

    return (
        <>
            <li className="reviews-sidebar__item">
                <a target="_blank" rel="noopener noreferrer" href={url}>{author}</a>
                <div>{recommendation.display}</div>
                <div>{score}</div>
            </li>

            {hasOpinions &&
                <ul className="reviews-sidebar__decision">
                    {opinions.map((opinion, i) => {
                        return <Opinion
                            key={i}
                            author={author}
                            opinion={opinion}
                        />
                    })}
                </ul>
            }
        </>
    )
}

Review.propTypes = {
    author: PropTypes.string.isRequired,
    score: PropTypes.number.isRequired,
    recommendation: PropTypes.shape({
        display: PropTypes.string.isRequired,
    }).isRequired,
    url: PropTypes.string.isRequired,
    opinions: PropTypes.arrayOf(PropTypes.object),
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
        <ul>
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
