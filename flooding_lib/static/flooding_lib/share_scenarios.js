$(document).ready(function () {
    var URL = '/flooding/scenario/share/action/';

    var update_element = function(element, action, message) {
	element.attr('data-action', action);
	element.html(message);
    }

    var click_handler = function (event) {
	event.preventDefault();

	var that = $(this);

	var handle_response = function(data) {
	    var parsed;
	    if (JSON !== undefined) {
		parsed = JSON.parse(data);
	    } else {
		parsed = eval(data); // IE7
	    }

	    update_element(that, parsed.action, parsed.message);
	}

	var action = that.attr("data-action");
	var scenario_id = that.attr("data-scenario-id");
	var project_id = that.attr("data-project-id");

	if (action !== undefined && action !== "") {
	    $.post(URL, {
		'action': action,
		'scenario_id': scenario_id,
		'project_id': project_id
	    }, handle_response);
	}
    }

    // Add the click handler to all <a>s with class "shareaction"
    $("a.shareaction").click(click_handler);
});
