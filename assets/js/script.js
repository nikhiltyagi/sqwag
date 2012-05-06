var context = context || {};

$(document).ready(function() {
  $('#add-friend').click(); // init the app
  
  $('#login-form form').ajaxForm({
    dataType: 'json',
    success: function(data) {
      if(data.status == 411) {
        alert(data.error);
      }
      else if(data.status == 1) {
        $('.close').click();
      }
    }
  });
});

function notify(data) {
  $('#console').text(data).fadeIn('slow');
}