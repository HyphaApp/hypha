import React from 'react';
import PropTypes from 'prop-types';
import { hot } from 'react-hot-loader'
import Switcher from '@components/Switcher'
import GroupByStatusDetailView from '@containers/GroupByStatusDetailView';


class SubmissionsByRoundApp extends React.Component {
    state = {
        detailOpen: false,
    };

    constructor(props) {
        super(props);
    }

    detailOpen = (state) => {
        this.setState({ style: { display: 'none' } })
        this.setState({ detailOpen: true })
    }

    detailClose = () => {
        this.setState({ style: {} })
        this.setState({ detailOpen: false })
    }

    render() {
        return (
            <>
                <Switcher selector='submissions-by-round-app-react-switcher' open={this.state.detailOpen} handleOpen={this.detailOpen} handleClose={this.detailClose} />

                <div style={this.state.style} ref={this.setOriginalContentRef} dangerouslySetInnerHTML={{ __html: this.props.pageContent }} />

                {this.state.detailOpen &&
                    <GroupByStatusDetailView roundId={this.props.roundId} />
                }
            </>
        )
    }
}

SubmissionsByRoundApp.propTypes = {
    roundId: PropTypes.number,
};


export default hot(module)(SubmissionsByRoundApp);
