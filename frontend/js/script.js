$(document).ready(function() {
  $('#sqwag-form form').ajaxForm({
    target: '#output',
    dataType: 'json',
    success: function(response) {
      console.log(response.message);
      $('#add-friend').click();
      $('.close').click();
    }
  });
});