const renderShellServers = _.template(
  $("#shell-servers-template")
    .remove()
    .text()
);

$(() =>
  apiCall("GET", "/api/v1/shell_servers")
    .success(function(data) {
      if (data.length > 0) {
        $("#shell-servers").html(renderShellServers({ servers: data }));
      }
    })
    .error(jqXHR =>
      apiNotify({ status: 0, message: jqXHR.responseJSON.message })
    )
);
