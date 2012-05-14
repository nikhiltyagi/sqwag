var context = context || {};

var SQ = {
  init: function() {
    $('#home').click();
  },
  
  fetchFeed: function() {
    $('#feed').click();
  },
  
  close: function() {
    $('.close').click();
  },
  
  notify: function(data) {
    $('#console').text(data).fadeIn('slow');
  },
  
  refresh: function() {
    window.location.reload();
  },
  
  bindLinks: function() {
    $('.js-load').click(function() {
      var tpl = $(this).attr('href').replace('#','');
      var url = '/assets/templates/' + tpl + '.html';
      $("#content").load(url);
      return false;
    });

    $('.js-link').click(function() {
      var link = $(this).attr('href');
      var jxhr = $.get(link).complete(function() {
        SQ.refresh();
      });
      return false;
    });
  },
  
  bindForms: function() {
     $('#login-form form').ajaxForm({
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          SQ.refresh();
        }
        else {
          SQ.notify(data.error);
          SQ.close();
        }
      }
    }); 
    
    $('#register-form form').ajaxForm({
      dataType: 'json',
      success: function(data) {
        if(data.status == 1) {
          SQ.notify(data.status);
        }
        else {
          SQ.notify(data.error);
        }
        SQ.close();
      }
    });
  },
  bindButtons: function() {
    $('.resqwag').live('click', function() {
      var square_id = $(this).data('id');
      $.post('/api/square/share', {'square_id' : square_id}, function() {
        SQ.notify('ho gaya!');
        SQ.fetchFeed();
      });
    });
  }
}

$(document).ready(function() {
  SQ.bindLinks();  
  SQ.bindForms(); 
  SQ.bindButtons();
  SQ.init();   
});