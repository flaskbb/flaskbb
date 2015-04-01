/**
 * management.js
 */
var csrftoken = $('meta[name=csrf-token]').attr('content');
$(document).ready(function() {

    $('#ban_users').click(function(event) {
        event.preventDefault();

        $.ajax({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            url: MANAGEMENT_URL + "/users/ban",
            method: "POST",
            data: { ids: [3, 4] },
            success: function(result) {
                console.log(result);
            }
        });
    })
});
