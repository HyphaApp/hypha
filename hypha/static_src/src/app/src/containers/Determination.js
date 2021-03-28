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
                            {d.isDraft && "[Draft]"}
                            {d.outcome} - {d.updatedAt.slice(0,10)} by {d.author}
                           {(!this.props.determinationDraftStatus || (this.props.determinationDraftStatus && !d.isDraft)) 
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
                {this.props.submission.actionButtons.showDeterminationButton && this.props.determinationDraftStatus && 
                <div className="status-actions">
                    <button onClick = {() =>  this.props.toggleDeterminationForm(true)} className="button button--primary button--half-width" style={{padding: '10px'}}>
                        Update draft
                    </button>
                </div>}
                { this.props.submission.actionButtons.showDeterminationButton && !this.props.determinationDraftStatus &&
                <div className="status-actions">
                    <button onClick = {() =>  this.props.toggleDeterminationForm(true)} className="button button--primary button--full-width" style={{padding: '10px'}}>
                        Add determination
                    </button>
                </div>}
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
})

export default connect(mapStateToProps, mapDispatchToProps)(DeterminationContainer)
