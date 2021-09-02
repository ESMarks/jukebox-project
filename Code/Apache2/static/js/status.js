var xhr = new XMLHttpRequest();
xhr.onload = get_data

function get_data(): {
  if(xhr.status === 200) {
    responseObject = JSON.parse(xhr.responseText);

    var mm1_Status = '';
    mm1_Status = responseObject.status;
    var el = document.getElementById('mm1');
    //var elText = el.firstChild.nodeValue;
    //elText = elText.replace('Unknown', mm1_Status);
    el.firstChild.nodeValue = mm1_Status;
  }
}

xhr.open('GET', 'http://raspberrypi/api/status', true);
xhr.send();
