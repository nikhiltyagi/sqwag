var context = context || {};

$(document).ready(function() {
  $('#add-friend').click(); // init the app

    
  $('#sqwag-form form').ajaxForm({
    dataType: 'json',
    success: function(response) {
      if(response.status==1){
        $('.close').click(); // close the modal window
        context.Squares.add(response.result);
      }  
    }
  });
});