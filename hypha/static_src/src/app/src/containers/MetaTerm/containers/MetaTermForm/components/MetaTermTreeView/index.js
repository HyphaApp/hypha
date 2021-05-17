import React from 'react'
import PropTypes from 'prop-types';
import './styles.scss';
import styles from './styleTreeView';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { withStyles } from '@material-ui/core/styles';


class MetaTermTreeView extends React.PureComponent {

    state = {
        expanded : []
    }

    createTreeItemList = (node) => {
        if("children" in node && node.children.length){
        return <TreeItem 
                nodeId={node.id} 
                label={node.name} 
                key={node.id} 
                classes= {{ 
                    root: this.props.classes.treeItemRoot, 
                    selected: this.props.classes.selected,
                    iconContainer: this.props.classes.iconContainer,
                  }}
              >
                {node.children.map(node => this.createTreeItemList(node))}
              </TreeItem>
        }
        else {
            return <TreeItem 
                      nodeId={node.id} 
                      label={node.name} 
                      key={node.id} 
                      classes= {{ 
                        root: this.props.classes.treeItemRoot, 
                        selected: this.props.classes.selected,
                        iconContainer: this.props.classes.iconContainer2,
                      }}
                      className="without-child-node"
                    />
        }
    }

    checkIfNodeSelectable = (selectedNodeId, node) => {
      // check selected node doesn't have children
        if(node.id == selectedNodeId && !node.children.length){
          return true
        }
        if(node.children.length){
          for(let child of node.children){
            if(this.checkIfNodeSelectable(selectedNodeId, child)) {
              return true
            }
          }
        }
        return false
    }

    handleSelect = (event, nodeIds) => {
      if (event.target.nodeName === "svg") {
        return;
      }
      const first = nodeIds[0];
      let isSelectable;

      for(let node of this.props.metaTermsStructure){
        isSelectable = this.checkIfNodeSelectable(first, node)
        if(isSelectable) break
      }

      if(isSelectable){
        if (this.props.selectedMetaTerms.includes(first)) {
          this.props.setSelectedMetaTerms(this.props.selectedMetaTerms.filter(id => id !== first));
        } else {
          this.props.setSelectedMetaTerms([first, ...this.props.selectedMetaTerms]);
        }
      }
    };

    handleToggle = (event, nodeIds) => {
      if (event.target.nodeName !== "svg") {
        return;
      }
      this.setState({expanded : nodeIds})
    };

    render(){
        return (
            <div className="react-modal metaTerm-form">
                <h4 className="react-modal__header-bar">Update Meta Terms</h4>
                <div className="react-modal__inner">
                    <button className="react-modal__close" onClick={this.props.closeForm}>&#10005;</button>
                    <p><strong>Meta Terms</strong></p>
                    <p>Meta Terms are hierarchical in nature.</p>
                    <div className="treeview">
                        <TreeView
                            className={this.props.classes.root}
                            defaultCollapseIcon={<ExpandMoreIcon />}
                            defaultExpandIcon={<ChevronRightIcon />}
                            selected={this.props.selectedMetaTerms}
                            onNodeSelect={this.handleSelect}
                            expanded={this.state.expanded}
                            onNodeToggle={this.handleToggle}
                            multiSelect
                        >
                            {this.props.metaTermsStructure.map(node => {
                                return this.createTreeItemList(node)
                            })}
                        </TreeView>
                        <button className="button button--primary button--top-space" onClick={this.props.updateMetaTerms}>Update</button>
                    </div>
                </div>
            </div>
        )
    }
}

MetaTermTreeView.propTypes = {
    metaTermsStructure: PropTypes.array,
    selectedMetaTerms: PropTypes.array,
    closeForm: PropTypes.func,
    setSelectedMetaTerms: PropTypes.func,
    updateMetaTerms: PropTypes.func
}

export default withStyles(styles)(MetaTermTreeView);
