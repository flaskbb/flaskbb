import { Modal } from "bootstrap";

var confirmModalElement = document.getElementById("confirmModal");
if (confirmModalElement) {
    // PS: Don't forget to use "type=button" for buttons:
    // https://stackoverflow.com/a/3315016
    // otherwise you gotta hijack the click event and add a preventDefault()

    confirmModalElement.addEventListener("show.bs.modal", function(event) {
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
