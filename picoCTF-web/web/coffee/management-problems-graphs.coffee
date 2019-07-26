ProblemSubmissionDoughnut = React.createClass
  componentDidMount: ->
    if @props.visible
      ctx = @context

      data = {
        datasets: [{
          data: [@props.invalid, @props.valid],
          backgroundColor: ["#F7464A", "#46BFBD"],
          hoverBackgroundColor: ["#FF5A5E", "#5AD3D1"]
        }],
        labels: [
          "Invalid Submissions",
          "Valid Submissions"
        ]
      }
      chart = new Chart( ctx, {
          type: 'doughnut',
          data: data,
          options: {
            animation: { animateRotate: false, animateScale: false }
          }
      })

  render: ->
    style =
      padding: 0
      margin: "auto"
      display: "block"

    <canvas height="200" ref={(c) => this.context = c.getContext('2d')} width="200" style={style}/>
