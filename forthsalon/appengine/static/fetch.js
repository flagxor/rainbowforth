var FETCH_START_TIMEOUT = 30 * 1000;
var fetch_timeout = FETCH_START_TIMEOUT;
var last_update = 0;

function GetText(url, callback) {
  var request = new XMLHttpRequest();
  request.onreadystatechange = function() {
    if (request.readyState == 4) {
      if (request.status == 200) {
        callback(request.responseText);
      } else {
        callback(null);
      }
    }
  }
  request.open('GET', url);
  request.send(null);
}

function FetchUpdates() {
  GetText('/haiku-fetch?start=' + encodeURIComponent(last_update),
      function(data) {
    if (data == null) {
      fetch_timeout *= 2;
      setTimeout(FetchUpdates, fetch_timeout);
      return;
    }
    var items = JSON.parse(data);
    if (items == 'stop') {
      alert('Please reload page!');
      return;
    }
    fetch_timeout = FETCH_START_TIMEOUT;
    if (items.length == 0) {
      setTimeout(FetchUpdates, fetch_timeout);
      return;
    }
    self.postMessage(items);
    for (var i = 0; i < items.length; i++) {
      if (last_update < items[i].last_modified) {
        last_update = items[i].last_modified;
      }
    }
    setTimeout(FetchUpdates, 0);
  });
}

FetchUpdates();
