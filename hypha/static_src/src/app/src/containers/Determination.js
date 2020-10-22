import React from 'react'
import SidebarBlock from '@components/SidebarBlock'
import PropTypes from 'prop-types'
import { connect } from 'react-redux'
import { getDeterminationButtonStatus, getDeterminationDraftStatus } from '@selectors/submissions'
import { toggleDeterminationFormAction, setCurrentDeterminationAction } from '@actions/submissions'
import './Determination.scss';

class DeterminationContainer extends React.PureComponent {

    render(){
        const determination = this.props.submission ? this.props.submission.determination : null
        const drafted = determination && 
        determination.count ? 
        determination.determinations[1] ? Math.max(determination.determinations[0].id, determination.determinations[1].id): determination.determinations[0].id 
        : null
        return <div className="determination-container">
            {determination  ? 
            <SidebarBlock title="Determination">
                {!determination.count ?
                    <p>Awaiting determination</p> 
                :
                <>
                   {determination.determinations.map((d, index) => {
                       return (
                           <p key={index}>
                            {this.props.determinationDraftStatus && d.id == drafted && 
                            "[Draft]"}{d.outcome}- {d.updatedAt.slice(0,10)} by {d.author}
                           {(!this.props.determinationDraftStatus || (this.props.determinationDraftStatus && d.id != drafted)) 
                            &&
                           <a onClick={() => { this.props.setCurrentDetermination(d.id); this.props.toggleDeterminationForm(true) }} title="Edit" >
                             <svg className="icon icon--pen"><use href="#pen"></use></svg>
                            </a> 
                            }
                           </p>
                       )
                   })}
                    
                </>
                }
                {this.props.determinationDraftStatus && 
                <div className="status-actions"><button onClick = {() =>  this.props.toggleDeterminationForm(true)} className="button button--primary button--half-width">Update Draft</button></div>}
                {!this.props.determinationDraftStatus && 
                this.props.submission.actions.some(action => action.display.includes("Determination")) && <div className="status-actions"><button onClick = {() =>  this.props.toggleDeterminationForm(true)} className="button button--primary button--full-width">Add determination</button></div>}
            </SidebarBlock>
           : null
           }
        </div>
    }
}

DeterminationContainer.propTypes = {
    submission: PropTypes.object,
    showDeterminationForm: PropTypes.bool,
    determinationDraftStatus: PropTypes.bool,
    toggleDeterminationForm: PropTypes.func,
    setCurrentDetermination: PropTypes.func,
}

const mapStateToProps = (state) => ({
    showDeterminationForm: getDeterminationButtonStatus(state),
    determinationDraftStatus: getDeterminationDraftStatus(state),
})

const mapDispatchToProps = (dispatch) => ({
    toggleDeterminationForm: (status) => dispatch(toggleDeterminationFormAction(status)),
    setCurrentDetermination: (reviewId) => dispatch(setCurrentDeterminationAction(reviewId)),
    // deleteReview: (reviewId, submissionID) => dispatch(deleteReviewAction(reviewId, submissionID)),
})

export default connect(mapStateToProps, mapDispatchToProps)(DeterminationContainer)