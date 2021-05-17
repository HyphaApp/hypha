import React from 'react'
import PropTypes from 'prop-types';
import { SidebarBlock } from '@components/SidebarBlock'
import Modal from '@material-ui/core/Modal';
import { withStyles } from '@material-ui/core/styles';
import MetaTermForm from './containers/MetaTermForm' 


const styles = {
    modal: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
  };

class MetaTerm extends React.PureComponent {

    state = {
        open : false
    }

    handleModalClose = () => {
        this.setState({open : false})
    }

    render(){
        const { classes } = this.props;
        return (
            <div className="metaterm-container">
                <SidebarBlock title={""}>
                    <div className="status-actions">
                        <button 
                            className="button button--primary button--full-width button--bottom-space metaterm-button" 
                            onClick={() => this.setState({open : true})}
                        >
                            Meta Terms
                        </button>
                        <Modal
                            className={classes.modal} 
                            open={this.state.open}
                        >
                            <>
                            <MetaTermForm 
                                submissionID={this.props.submissionID} 
                                closeForm={() => this.setState({open: false})}
                            />
                            </>
                        </Modal>
                    </div>
                </SidebarBlock>
            </div>
        )
    }
}

MetaTerm.propTypes = {
    submissionID: PropTypes.number,
}

export default withStyles(styles)(MetaTerm);
