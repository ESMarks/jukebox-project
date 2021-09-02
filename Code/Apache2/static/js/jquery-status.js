$(document).ready(function(){
  new get_data();
  });

function get_data(){
  var status = $.ajax({//ajax
                       type: "GET",
                       url: "http://jukebox.markslab.mynetgear.com/api/status",
                       async: false
                       }).always(function(){
                            setTimeout(get_data, 1000);
                       }).responseText;
  responseObject = JSON.parse(status)
  var el = document.getElementById("mm1");
  el.firstChild.nodeValue = responseObject.status;
}
