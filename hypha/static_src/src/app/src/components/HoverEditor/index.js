import React from 'react';
import TinyMCE from '@common/components/TinyMCE';
import Button from '@material-ui/core/Button';
import {withStyles} from '@material-ui/core/styles';
import Tooltip from '@material-ui/core/Tooltip';
import PropTypes from 'prop-types';
import LoadingPanel from '@components/LoadingPanel';
import './styles.scss';

const styles = {
    submitButton: {
        minWidth: 150,
        backgroundColor: '#0c72a0 !important ',
        color: 'white',
        marginRight: 10,
        height: 40
    },
    cancelButton: {
        minWidth: 150,
        marginRight: 10,
        height: 40
    }
};
class HoverEditor extends React.Component {
    static propTypes = {
        onChange: PropTypes.func,
        charLimit: PropTypes.number,
        value: PropTypes.string,
        classes: PropTypes.object,
        readOnly: PropTypes.bool,
        label: PropTypes.string
    };

    state = {
        isEditorOpened: false,
        value: this.props.value ? this.props.value : '',
        loading: false
    };

    toggleEditor = (status) => this.setState({isEditorOpened: status});

    updateValue = (name, newValue) => {
        this.setState({value: newValue});
    };

    componentDidUpdate(prevProps, prevState) {
        if (this.props.value !== prevProps.value) {
            this.toggleEditor(false);
            this.setState({loading: false});
            this.updateValue('', this.props.value ? this.props.value : '');
        }
    }

    render() {
        const {classes} = this.props;

        return (<div>
            {!this.state.loading ? this.state.isEditorOpened ?
                <div className={'editor-container'}>
                    <TinyMCE
                        label={this.props.label}
                        onChange={this.updateValue}
                        value={this.state.value ? this.state.value : this.props.value}
                        init={{
                            charLimit: this.props.charLimit ? this.props.charLimit : 500,
                            setup: function (editor) {
                                editor.on('keyDown', function (e) {
                                    var tinymax; var tinylen;
                                    tinymax = this.settings.charLimit;
                                    tinylen = (this.getContent().replace(/<[^>]+>|&nbsp;/g, '').length) + 1;
                                    if (tinylen > tinymax && e.keyCode != 8 && e.keyCode != 46) {
                                        this.setContent(this.getContent().replace(/<[^>]+>/g, '').slice(0, tinymax));
                                        e.preventDefault();
                                        e.stopPropagation();
                                        return false;
                                    }
                                });
                            }
                        }}
                    />
                    <Button
                        variant="contained"
                        size={'small'}
                        classes={{root: classes.submitButton}}
                        onClick={() => {this.setState({loading: true}); this.props.onChange(this.state.value); this.toggleEditor(false);}}
                    >
                        Submit
                    </Button>
                    <Button
                        variant="contained"
                        size={'small'}
                        classes={{root: classes.cancelButton}}
                        onClick={() => {this.updateValue('', this.props.value ? this.props.value : ''); this.toggleEditor(false);}}
                    >
                        Cancel
                    </Button>
                    <span className={'content-length'}>{this.state.value ? this.state.value.replace(/<[^>]+>|&nbsp;/g, '').length : this.props.value.replace(/<[^>]+>|&nbsp;/g, '').length}/500</span>
                </div>
                :
                this.props.readOnly
                    ?
                    <div className="summary-content__readonly">
                        {this.props.value.replace(/<[^>]+>/g, '')
                            ? <p dangerouslySetInnerHTML={{__html: this.props.value}} />
                            : <p>{this.props.label}</p> }
                    </div>
                    :
                    <Tooltip title={<span style={{fontSize: '15px'}}>Click to edit</span>} placement="top-end" arrow>
                        <div onClick={() => this.toggleEditor(true)} className="summary-content__editable">
                            {this.props.value.replace(/<[^>]+>/g, '') ? <p dangerouslySetInnerHTML={{__html: this.props.value}}/> : <p>{this.props.label}</p>}
                        </div>
                    </Tooltip>

                : <LoadingPanel/>}
        </div>);
    }
}

export default withStyles(styles)(HoverEditor);
