var video;
window.addEventListener('DOMContentLoaded', function() {
  video = document.getElementById("live");

  if (!navigator.getUserMedia) {
    navigator.getUserMedia = navigator.webkitGetUserMedia;
  }
  navigator.getUserMedia({'video': true},
    function(stream) {
      video.src = window.webkitURL.createObjectURL(stream);
    },
    function(err) {
      console.log("Unable to get video stream!");
    }
    );
  snap();
});

function is_marker(data, pos) {
  var red = data[pos + 0];
  var green = data[pos + 1];
  var blue = data[pos + 2];
  return green * 1.4 < Math.min(red, blue) && red > 80 && blue > 50;
}

function is_marker_loose(data, pos) {
  if (is_marker(data, pos)) return true;
  var red = data[pos + 0];
  var green = data[pos + 1];
  var blue = data[pos + 2];
  return green * 1.2 < Math.min(red, blue) && red > 30 && blue > 30;
}

function unmark(data, pos) {
  data[pos + 0] = 0;
  data[pos + 1] = 255;
  data[pos + 2] = 0;
}

tile_labels = [
'x', 'y', 't',
  'push', 'pop',
  'dup', 'over', '2dup', 'drop', 'swap',
  '=', '<>', '<', '>', '<=', '>=',
  'and', 'or', 'not',
  'min', 'max',
  '+', '-', '*', '/', 'mod',
  'pow', 'atan2', 'negate',
  'sin', 'cos', 'tan',
  'log', 'exp', 'sqrt',
  'floor', 'ceil', 'abs',
  'pi', 'z+', 'z-', 'z*',
  'random', ':', ';',
  'A', 'B', 'C', 'D',
  '0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9',
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
  '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
  '21', '22', '23', '24', '25',
  ];

function decode_id(id) {
  if (id < tile_labels.length) {
    return tile_labels[id];
  } else {
    return '';
  }
}

function flood(data, width, height, i, j) {
  var count = 0;
  var x = 0;
  var y = 0;
  var pending = [];
  pending.push([i, j]);
  while (pending.length) {
    var item = pending.pop();
    if (item[0] < 0 || item[1] < 0 ||
        item[0] >= width || item[1] >= height) continue;
    var pos = (item[0] + item[1] * width) * 4;
    if (!is_marker_loose(data, pos)) continue;
    x += item[0];
    y += item[1];
    count++;
    unmark(data, pos);
    pending.push([item[0] - 1, item[1]]);
    pending.push([item[0] + 1, item[1]]);
    pending.push([item[0], item[1] - 1]);
    pending.push([item[0], item[1] + 1]);
  }
  return [x / count, y / count, count];
}

function Distance2(a, b) {
  var dx = a[0] - b[0];
  var dy = a[1] - b[1];
  return dx * dx + dy * dy;
}

function MergeClose(markers) {
  var ret = []; 
  for (var i = 0; i < markers.length; i++) {
    if (markers[i][2] == 0) continue;
    var p = [markers[i][0] * markers[i][2],
      markers[i][1] * markers[i][2], markers[i][2]];
    for (var j = i + 1; j < markers.length; j++) {
      if (markers[j][2] == 0) continue;
      var dist = Distance2(markers[i], markers[j]);
      if (dist < 100) {
        p[0] += markers[j][0] * markers[j][2];
        p[1] += markers[j][1] * markers[j][2];
        p[2] += markers[j][2];
        markers[j][2] = 0;
      }
    }
    p[0] /= p[2];
    p[1] /= p[2];
    ret.push(p);
  }
  return ret;
}

function DropSmall(markers) {
  var ret = []; 
  for (var i = 0; i < markers.length; i++) {
    if (markers[i][2] > 100) {
      ret.push(markers[i]);
    }
  }
  return ret;
}

function Sample(data, width, height, i, j) {
  if (i < 0 || j < 0 || i >= width || j >= height) {
    return 0;
  } else {
    var pos = (i + j * width) * 4;
    return data[pos + 0] * 0.2126 + 
      data[pos + 1] * 0.7152 + 
      data[pos + 2] * 0.0722;
  }
}

function SubSample(data, width, height, i, j) {
  var xf = Math.floor(i); 
  var yf = Math.floor(j); 
  var xp = i - xf;
  var yp = j - yf;
  return Sample(data, width, height, xf, yf) * (1 - xp) * (1 - yp) +
    Sample(data, width, height, xf + 1, yf) * xp * (1 - yp) +
    Sample(data, width, height, xf, yf + 1) * (1 - xp) * yp +
    Sample(data, width, height, xf + 1, yf + 1) * xp * yp;
}

/*
function BarSample(data, width, height, pair, index) {
  var sx = (pair[1][0] - pair[0][0]) / 3;
  var sy = (pair[1][1] - pair[0][1]) / 3;
  return SubSample(data, width, height,
      pair[0][0] + sx * index,
      pair[0][1] + sy * index);
}

function DecodeBarcodes(data, width, height, pairs) {
  var barcodes = [];
  pair_loop:
    for (var i = 0; i < pairs.length; i++) { 
      var pair = pairs[i];
      if (BarSample(data, width, height, pair, 1) > 
          BarSample(data, width, height, pair, 2)) {
            pair = [pair[1], pair[0]];
          }

      var black = BarSample(data, width, height, pair, 1);
      var white = BarSample(data, width, height, pair, 2);
      var mid = (black + white) / 2;
      var gap = (white - mid) / 2;
      if (gap < 5) continue;
      //barcodes.push([pair[0][0], pair[0][1], 'hi']);
      //continue;

      var value = 0;
      for (var offset = 0; offset < 4; offset++) {
        var a = BarSample(data, width, height, pair, -offset - 1);
        if (a >= mid - gap && a <= mid + gap) continue pair_loop;
        var b = BarSample(data, width, height, pair, offset + 4);
        if (b >= mid - gap && b <= mid + gap) continue pair_loop;
        if (a > mid && b > mid) continue pair_loop;
        if (a < mid && b < mid) continue pair_loop;
        if (b > mid) {
          value |= (1 << offset);
        }
      }
      var lb = decode_id(value);
      if (lb != '') {
        barcodes.push([pair[0][0], pair[0][1], lb]);
      }
    }
  return barcodes;
}
*/

function snap() {
  live = document.getElementById("live");
  snapshot = document.getElementById("snapshot");
  processed = document.getElementById("processed");

  // Make the canvas the same size as the target
  snapshot.width = processed.clientWidth;
  snapshot.height = processed.clientHeight;

  // Draw a frame of the live video onto the canvas
  c = snapshot.getContext("2d");
  c.drawImage(live, 0, 0, snapshot.width, snapshot.height);

  c2 = processed.getContext("2d");

  var idata = c.getImageData(0, 0, snapshot.width, snapshot.height);
  var markers = [];
  for (var j = 0; j < snapshot.width; j++) {
    for (var i = 0; i < snapshot.width - 1; i++) {
      var pos = (i + j * snapshot.width) * 4;
      if (is_marker(idata.data, pos)) {
        markers.push(
            flood(idata.data, snapshot.width, snapshot.height, i, j));
      }
    }
  }

  markers = MergeClose(markers);
  markers = DropSmall(markers); 

  c2.fillStyle= 'black';
  c2.fillRect(0, 0, snapshot.width, snapshot.height);
  c2.putImageData(idata, 0, 0);
  for (var i = 0; i < markers.length; i++) {
    c2.fillStyle= 'blue';
    c2.fillRect(markers[i][0] - 2, markers[i][1] - 2, 4, 4);
  }

  setTimeout(snap, 30);
}
