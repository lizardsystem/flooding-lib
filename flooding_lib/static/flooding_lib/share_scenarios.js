$(document).ready(function () {
    var URL = '/flooding/scenario/share/action/';

    var click_handler = function (event) {
	var that = $(this);

	var handle_response = function(data) {
	    var parsed;
	    if (JSON !== undefined) {
		parsed = JSON.parse(data);
	    } else {
		parsed = eval(data); // IE7
	    }

	    that.attr('data-action', parsed.action);

	    if (parsed.is_url) {
		that.html('<a href="#">'+parsed.message+'</a>');
	    } else {
		that.html(parsed.message);
	    }
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

    var prevent_action_handler = function (event) {
	event.preventDefault();
    }

    // Add the click handler to all elements with class "shareaction"
    $(".shareaction").click(click_handler);
    // Add the prevent action handler to any a's inside it
    $(".shareaction a").click(prevent_action_handler);

});
