renderShellServers = _.template($("#shell-servers-template").remove().text())

$ ->
  apiCall "GET", "http://localhost:5000/api/v1/user/shell_servers", {}

  .done (resp) ->
    switch resp.status
      when 0
          apiNotify resp
      when 1
        if resp.data
          $("#shell-servers").html renderShellServers({servers: resp.data})
