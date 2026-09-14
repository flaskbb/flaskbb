import { Modal } from "bootstrap";

var confirmModalElement = document.getElementById("confirmModal");
if (confirmModalElement) {
    // Usage:
    // <button type="button" class="btn btn-icon" data-bs-toggle="modal" data-bs-target="#confirmModal">
    //     <span class="far fa-trash-alt text-danger" data-bs-toggle="tooltip" title="{% trans %}Delete{% endtrans %}"></span>
    // </button>
    // PS: Don't forget to use "type=button" for buttons - otherwise you'll submit the form before the modal pops up
    //     or you gotta hijack the click event and add a preventDefault() to the form

    confirmModalElement.addEventListener("show.bs.modal", function(event) {
        if(event.relatedTarget == undefined || event.relatedTarget.dataset.bsTarget !== "#confirmModal") {
            return
        }

        // Get the instance of this modal
        let confirmModal = Modal.getInstance(confirmModalElement);

        // Button that triggered the modal
        let button = event.relatedTarget;

        // form of the button that triggered this modal
        let form = button.closest("form");

        // the confirm button of the modal
        let confirmButton = confirmModalElement.querySelector(".confirmBtn");
        confirmButton.addEventListener(
            "click",
            function(e) {
                e.preventDefault();
                if (form.checkValidity()) {
                    form.submit();
                    confirmModal.hide();
                } else {
                    confirmModal.hide();
                    form.reportValidity();
                }
            },
            {
                once: true,
            }
        );
    });
}

// hx-confirm asks through the same modal instead of window.confirm()
document.addEventListener("htmx:confirm", (event) => {
    const modalElement = document.getElementById("confirmModal");
    if (!modalElement || !event.detail.elt.hasAttribute("hx-confirm")) {
        return;
    }
    event.preventDefault();

    const modal = Modal.getOrCreateInstance(modalElement);
    const listeners = new AbortController();
    modalElement.querySelector(".confirmBtn").addEventListener(
        "click",
        (e) => {
            e.preventDefault();
            modal.hide();
            event.detail.issueRequest(true);
        },
        { signal: listeners.signal }
    );
    modalElement.addEventListener("hidden.bs.modal", () => listeners.abort(), { once: true });
    modal.show();
});
