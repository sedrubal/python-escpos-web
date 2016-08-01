var ws;
var wsurl = document.URL.replace(/^http/g, 'ws').split('#')[0].split('?')[0].replace(/\/$/g, '') + '/ws/';
console.log("Websocket URL is " + wsurl);

function printText() {
  var text = document.getElementById('text').value;
  send({
    'text': text,
    'cut': document.getElementById('cut').checked,
  });
}

function printBarcode() {
  var barcode = document.getElementById('barcode').value;
  var barcode_type = document.getElementById('barcode-type').value;
  send({
    'barcode': barcode,
    'barcode-type': barcode_type,
    'cut': document.getElementById('cut').checked,
  });
}

function printImage() {
  var file = document.getElementById('image').files[0];
  var reader = new FileReader();
  var rawData = new ArrayBuffer();            
  reader.loadend = function() {};
  reader.onload = function(e) {
    rawData = e.target.result;
    data = {
      'image': btoa(rawData),
      'cut': document.getElementById('cut').checked,
    };
    if (document.getElementById('image-resize').checked) {
      data['image-resize'] = document.getElementById('image-resize-value').value;
    }
    send(data);
  };
  reader.readAsBinaryString(file);
}

function cut() {
  send({
    'cut': true,
  })
}

function reset() {
  send({
    'set': '',
  })
}

window.onload = function onLoad() {
  connect(wsurl);
};
window.onbeforeunload = function() {
  ws = undefined; // don't reconnect while reloading page
};

function connect(wsurl) {
  if (ws == undefined || ws.readyState == ws.CLOSED) {
    ws = new WebSocket(wsurl);
    ws.onopen = onopen;
    ws.onmessage = onmessage;
    ws.onclose = onclose;
    ws.onerror = function (error) {
      console.log('WebSocket Error ' + error);
      update_status();
    };
    console.log("Connected");
    update_status();
  }
}

function onopen() {
  update_status();
};

function onmessage(evt) {
  var message = JSON.parse(evt.data);
  console.log(message)
  var msgbox = document.getElementById('msgbox');
  if (message.hasOwnProperty('error')) {
    msgbox.classList.remove('hide');
    msgbox.classList.remove('success');
    msgbox.classList.add('danger');
    msgbox.innerText = message.error;
  } else if (message.hasOwnProperty('success')) {
    inpts = [document.getElementById('text'), document.getElementById('barcode'), document.getElementById('image')];
    for (var i = 0, l = inpts.length; i < l; i++) {
      var inpt = inpts[i];
      inpt.value = "";
    }
    msgbox.classList.remove('hide');
    msgbox.classList.remove('danger');
    msgbox.classList.add('success');
    msgbox.innerText = message.success;
  }
  document.getElementById('loading').classList.add('hide');
};

function onclose() {
  if (ws != undefined && ws.readyState == ws.CLOSED) {
    console.log("Disconnected");
    update_status();
    setTimeout(connect(wsurl), 1000);
  }
}

function send(message) {
  ws.send(JSON.stringify(message));
  console.log(message);
  document.getElementById('msgbox').classList.add('hide');
  document.getElementById('loading').classList.remove('hide');
}

function update_status() {
  if (ws.readyState == ws.OPEN) {
    document.getElementById('status').innerText = 'connected';
  } else {
    document.getElementById('status').innerText = 'connecting...';
  }
}
