function toastHandler() {
    return {
        toasts: [],
        visible: [],
        add(toast) {
            toast.id = Date.now();
            this.toasts.push(toast);
            this.fire(toast.id);
        },
        fire(id) {
            this.visible.push(this.toasts.find((toast) => toast.id == id));
            const timeShown = 2000 * this.visible.length;
            setTimeout(() => {
                this.remove(id);
            }, timeShown);
        },
        remove(id) {
            const toast = this.visible.find((toast) => toast.id == id);
            const index = this.visible.indexOf(toast);
            this.visible.splice(index, 1);
        },
    };
}

(function () {
    htmx.on("showMessage", (e) => {
        let message_detail = { type: "info", text: "🎬 " + e.detail.value };
        dispatchEvent(
            new CustomEvent("notice", {
                detail: message_detail,
                bubbles: true,
                cancelable: true,
                composed: true,
            })
        );
    });
})();
