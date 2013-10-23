function run(url)
{
	$.ajax(
	{
		type: 'POST',
		url: url,
	});
}

var ws;
function connect(url)
{

	ws = new WebSocket('ws://' + window.location.host + url);
	ws.onmessage = function(msg)
	{
		var packet = JSON.parse(msg.data);
		if (packet.host)
		{
			if (packet.data)
			{
				var pre = $('pre[host="' + packet.host + '"]');
				var addition = $(document.createTextNode(packet.data));
				pre.append(addition);
				pre.parent().scrollTop(pre.height());

				var h2 = $('h2[host="' + packet.host + '"]');
				h2.attr('class', 'converging');
			}
			else if (packet.status)
			{
				var h2 = $('h2[host="' + packet.host + '"]');
				h2.attr('class', packet.status);
			}
		}
		else if (packet.status)
		{
			$('#run')
				.attr('class', packet.status)
				.text(packet.status.charAt(0).toUpperCase() + packet.status.slice(1));
		}
	};

	ws.onclose = function()
	{
		setTimeout(function()
		{
			if (ws != null && ws.readyState != 1)
				connect(url);
		}, 2000);
	};
}

$(document).ready(function()
{
	$('h2').click(function()
	{
		var console = $(this).next();
		console.toggleClass('expanded');
		console.scrollTop(console.children().first().height());
	});

	$('pre').each(function()
	{
		var $this = $(this);
		$this.parent().scrollTop($this.height());
	});
});
