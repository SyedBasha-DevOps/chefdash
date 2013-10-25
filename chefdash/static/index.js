function run(url)
{
	$.ajax(
	{
		type: 'POST',
		url: url,
	});
}

function h2_clicked()
{
	var console = $(this).next();
	console.toggleClass('expanded');
	console.scrollTop(console.children().first().height());
}

function add(node, $parent, click)
{
	if ($('h2[host="' + node + '"]').length > 0)
		return;

	var $h2 = $(
		'<h2 class="ready" host="' + node + '">'
		+ '<button class="ready">ready</button> ' + node
		+ '</h2>'
	);
	$parent.prepend($h2);

	$h2.click(h2_clicked);
	$h2.find('button').click(function(event)
	{
		event.stopPropagation();
		click();
	});

	$h2.after(
		'<div class="console">'
		+ '<pre host="' + node + '"></pre>'
		+ '</div>'
	);
}

var ws;
function connect(url)
{
	ws = new WebSocket((window.location.protocol == 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + url);
	ws.onmessage = function(msg)
	{
		var packet = JSON.parse(msg.data);
		if (packet.host)
		{
			var h2 = $('h2[host="' + packet.host + '"]');
			if (h2.length > 0)
			{
				if (packet.data)
				{
					var pre = $('pre[host="' + packet.host + '"]');
					var addition = $(document.createTextNode(packet.data));
					pre.append(addition);
					pre.parent().scrollTop(pre.height());
				}

				if (packet.status)
				{
					h2.attr('class', packet.status);
					h2.find('button').text(packet.status);
					if (packet.status != 'error' && packet.status != 'ready')
					{
						var pre = $('pre[host="' + packet.host + '"]');
						pre.text('');
					}
				}
			}
		}
		else if (packet.status)
		{
			$('#run')
				.attr('class', packet.status)
				.text(packet.status);
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
	$('h2 button').click(function(event)
	{
		event.stopPropagation();
	});

	$('h2').click(h2_clicked);

	$('pre').each(function()
	{
		var $this = $(this);
		$this.parent().scrollTop($this.height());
	});
});
