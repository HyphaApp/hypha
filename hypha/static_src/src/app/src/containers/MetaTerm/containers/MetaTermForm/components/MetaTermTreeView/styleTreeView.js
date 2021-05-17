export default theme => ({
    root: {
        maxWidth: 400,
    },
    treeItemRoot: {
      "& > .MuiTreeItem-content > .MuiTreeItem-label": {
        display: "flex",
        alignItems: "center",
        padding: "4px 0",
        background: "transparent !important",
        pointerEvents: "none"
      },
      "&.MuiTreeItem-root.without-child-node > .MuiTreeItem-content  > .MuiTreeItem-label::before ": {
        content: "''",
        display: "inline-block",
        width: 12,
        height: 12,
        marginRight: 8,
        border: "1px solid #ccc",
        background: "white",
      },
    },
    iconContainer: {
      paddingRight: '7px',  
      "& > svg": {
        "&:hover": {
          opacity: 0.6
        },
      },
    },
    iconContainer2: {
      display: "none"
    },
    selected: {
      "&.MuiTreeItem-root.without-child-node > .MuiTreeItem-content  > .MuiTreeItem-label::before": {
        background: "#0c72a0",
        border: "1px solid transparent"
        }
    }
});
